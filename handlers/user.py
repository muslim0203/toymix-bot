"""
User handlers for catalog browsing and interactions
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards.user_kb import (
    get_main_menu_keyboard,
    get_categories_keyboard,
    get_toy_pagination_keyboard,
    get_order_confirmation_keyboard
)
from services.catalog_service import CatalogService
from services.category_service import CategoryService
from services.order_contact_service import OrderContactService
from services.stats_service import StatsService
from services.favorites_service import FavoritesService
from database.db import get_db_session
from config import ADMIN_IDS

logger = logging.getLogger(__name__)
router = Router()


class OrderStates(StatesGroup):
    """FSM states for order process"""
    waiting_confirmation = State()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command"""
    welcome_text = (
        "👋 Assalomu alaykum!\n\n"
        "Yaypan Toymix botiga xush kelibsiz! 🎁\n\n"
        "Bizning katalogimizdan o'yinchoqlarni ko'rib chiqing va buyurtma bering."
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard()
    )


@router.message(F.text == "🏠 Bosh menyu")
async def show_main_menu(message: Message):
    """Show main menu"""
    welcome_text = (
        "👋 Assalomu alaykum!\n\n"
        "Yaypan Toymix botiga xush kelibsiz! 🎁\n\n"
        "Bizning katalogimizdan o'yinchoqlarni ko'rib chiqing va buyurtma bering."
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard()
    )


@router.message(F.text == "⬅️ Orqaga")
async def go_back_from_categories(message: Message):
    """Go back from categories to main menu"""
    await show_main_menu(message)


@router.message(F.text == "📦 Katalog")
async def show_categories(message: Message):
    """Show categories list"""
    db = get_db_session()
    try:
        categories = CategoryService.get_active_categories(db)
        
        if not categories:
            await message.answer(
                "❌ Hozircha kategoriyalar mavjud emas.\n\n"
                "Tez orada kategoriyalar qo'shiladi!",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        categories_text = "📂 <b>Kategoriyalarni tanlang:</b>"
        await message.answer(
            categories_text,
            parse_mode="HTML",
            reply_markup=get_categories_keyboard(categories)
        )
        
    except Exception as e:
        logger.error(f"Error showing categories: {e}", exc_info=True)
        await message.answer(
            "❌ Xatolik yuz berdi. Qayta urinib ko'ring.",
            reply_markup=get_main_menu_keyboard()
        )
    finally:
        db.close()


@router.message(F.text.startswith("📂 ") & ~F.text.in_(["📂 Kategoriya qo'shish"]))
async def show_category_toys(message: Message):
    """Show paginated toys in selected category (10 per page)"""
    category_name = message.text.replace("📂 ", "").strip()
    
    db = get_db_session()
    try:
        category = CategoryService.get_category_by_name(db, category_name)
        
        if not category or not category.is_active:
            await message.answer(
                "❌ Kategoriya topilmadi.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        # Get paginated toys for this category (page 0, 10 items per page)
        # IMPORTANT: This uses the service method which properly queries the database
        toys, total_count = CatalogService.get_active_toys_by_category(
            db, 
            category_id=category.id, 
            page=0,  # Start from page 0
            page_size=10
        )
        
        # Debug logging to verify products are found
        logger.info(f"Category {category.id} ({category.name}): Found {total_count} total toys, showing {len(toys)} on page 1")
        
        if not toys:
            await message.answer(
                f"😔 '{category.name}' kategoriyasida hozircha o'yinchoqlar yo'q.",
                reply_markup=get_categories_keyboard(CategoryService.get_active_categories(db))
            )
            return
        
        # Show category header
        await message.answer(
            f"📦 <b>{category.name}</b>\n\n"
            f"📄 Sahifa 1 / {((total_count + 9) // 10) if total_count > 0 else 1}\n"
            f"📊 Jami: {total_count} ta o'yinchoq",
            parse_mode="HTML"
        )
        
        # Show each toy on this page
        import asyncio
        for idx, toy in enumerate(toys):
            try:
                # Show toy (without individual pagination buttons, we'll add category pagination at the end)
                await show_toy_for_category_page(message, toy, category.id, db=db)
                
                # Small delay between messages to avoid flood limit
                if idx < len(toys) - 1:  # Don't delay after last toy
                    await asyncio.sleep(0.3)
                    
            except Exception as e:
                logger.error(f"Error showing toy {toy.id}: {e}", exc_info=True)
                # Continue with next toy even if one fails
                continue
        
        # Add pagination keyboard at the end
        from keyboards.category_pagination_kb import get_category_pagination_keyboard
        pagination_kb = get_category_pagination_keyboard(
            category_id=category.id,
            page=0,
            total_count=total_count,
            page_size=10
        )
        
        await message.answer(
            f"📄 Sahifa 1 / {((total_count + 9) // 10) if total_count > 0 else 1}",
            reply_markup=pagination_kb
        )
        
    except Exception as e:
        logger.error(f"Error showing category toys: {e}", exc_info=True)
        await message.answer(
            "❌ Xatolik yuz berdi.",
            reply_markup=get_main_menu_keyboard()
        )
    finally:
        db.close()


@router.callback_query(F.data.startswith("catpage:"))
async def handle_category_pagination(callback: CallbackQuery):
    """Handle category pagination - navigate between pages of products in a category"""
    try:
        # Format: catpage:{category_id}:{page}
        parts = callback.data.split(":")
        if len(parts) != 3:
            await callback.answer("❌ Xatolik", show_alert=True)
            return
        
        category_id = int(parts[1])
        page = int(parts[2])  # 0-indexed
        
        db = get_db_session()
        try:
            category = CategoryService.get_category_by_id(db, category_id)
            if not category:
                await callback.answer("❌ Kategoriya topilmadi", show_alert=True)
                return
            
            # Get paginated toys for this category and page
            # IMPORTANT: This uses the service method which properly queries the database
            toys, total_count = CatalogService.get_active_toys_by_category(
                db,
                category_id=category_id,
                page=page,
                page_size=10
            )
            
            # Debug logging
            logger.info(f"Category {category_id} page {page}: Found {total_count} total toys, showing {len(toys)} on this page")
            
            if not toys:
                await callback.answer("❌ O'yinchoqlar topilmadi", show_alert=True)
                return
            
            # Delete previous pagination message if it exists
            try:
                await callback.message.delete()
            except:
                pass
            
            # Calculate total pages
            total_pages = (total_count + 9) // 10 if total_count > 0 else 1
            current_page_display = page + 1  # Display as 1-indexed
            
            # Show category header
            await callback.message.answer(
                f"📦 <b>{category.name}</b>\n\n"
                f"📄 Sahifa {current_page_display} / {total_pages}\n"
                f"📊 Jami: {total_count} ta o'yinchoq",
                parse_mode="HTML"
            )
            
            # Show each toy on this page
            import asyncio
            for idx, toy in enumerate(toys):
                try:
                    await show_toy_for_category_page(callback.message, toy, category_id, db=db)
                    
                    # Small delay between messages
                    if idx < len(toys) - 1:
                        await asyncio.sleep(0.3)
                        
                except Exception as e:
                    logger.error(f"Error showing toy {toy.id}: {e}", exc_info=True)
                    continue
            
            # Add pagination keyboard at the end
            from keyboards.category_pagination_kb import get_category_pagination_keyboard
            pagination_kb = get_category_pagination_keyboard(
                category_id=category_id,
                page=page,
                total_count=total_count,
                page_size=10
            )
            
            await callback.message.answer(
                f"📄 Sahifa {current_page_display} / {total_pages}",
                reply_markup=pagination_kb
            )
            
            await callback.answer()
            
        finally:
            db.close()
            
    except (ValueError, IndexError) as e:
        logger.error(f"Error in category pagination: {e}", exc_info=True)
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)


@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery):
    """Go back to category list from pagination"""
    try:
        db = get_db_session()
        try:
            categories = CategoryService.get_active_categories(db)
            
            if not categories:
                await callback.message.answer(
                    "❌ Hozircha kategoriyalar mavjud emas.",
                    reply_markup=get_main_menu_keyboard()
                )
                await callback.answer()
                return
            
            # Delete current message
            try:
                await callback.message.delete()
            except:
                pass
            
            await callback.message.answer(
                "📂 <b>Kategoriyalarni tanlang:</b>",
                parse_mode="HTML",
                reply_markup=get_categories_keyboard(categories)
            )
            await callback.answer()
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error going back to categories: {e}", exc_info=True)
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)


@router.callback_query(F.data.startswith("toy_page_"))
async def handle_toy_pagination(callback: CallbackQuery):
    """Handle toy pagination - navigate between individual toys (legacy, kept for backward compatibility)"""
    try:
        # Format: toy_page_{category_id}_{page}
        parts = callback.data.split("_")
        category_id = int(parts[2])
        page = int(parts[3])
        
        db = get_db_session()
        try:
            category = CategoryService.get_category_by_id(db, category_id)
            if not category:
                await callback.answer("❌ Kategoriya topilmadi", show_alert=True)
                return
            
            # Get ALL toys for this category (ordered)
            all_toys = db.query(Toy).filter(
                Toy.is_active == True,
                Toy.category_id == category_id
            ).order_by(
                Toy.created_at.desc()
            ).all()
            
            if not all_toys:
                await callback.answer("❌ O'yinchoqlar topilmadi", show_alert=True)
                return
            
            total_pages = len(all_toys)
            
            # Validate page number
            if page < 1:
                page = 1
            elif page > total_pages:
                page = total_pages
            
            # Get toy at current page (1-indexed, so subtract 1)
            toy = all_toys[page - 1]
            
            # Show toy with pagination
            await show_toy(callback, toy, category_id, page, total_pages, category_id, db=db)
            await callback.answer()
            
        finally:
            db.close()
            
    except (ValueError, IndexError) as e:
        logger.error(f"Error in pagination: {e}", exc_info=True)
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)


async def show_toy_for_category_page(message: Message, toy, category_id: int, db=None):
    """
    Display a toy for category page view (without individual toy pagination)
    Shows only cart/favorites/buy buttons, no toy-level pagination
    """
    from services.media_service import MediaService
    
    # Format message
    category_name = toy.category.name if toy.category else "Kategoriyasiz"
    message_text = (
        f"📦 <b>{toy.title}</b>\n"
        f"🧸 Kategoriya: {category_name}\n\n"
        f"💰 Narxi: {toy.price}\n\n"
        f"📝 {toy.description}"
    )
    
    # Get user ID for favorites check
    user_id = message.from_user.id if message.from_user else None
    bot = message.bot
    
    if user_id and db:
        is_favorite = FavoritesService.get_favorite(db, user_id, toy.id) is not None
    else:
        is_favorite = False
    
    # Build keyboard (only cart/favorites/buy, no pagination)
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    
    builder = InlineKeyboardBuilder()
    
    # Cart and favorites buttons
    builder.add(InlineKeyboardButton(
        text="➕ Savatchaga qo'shish",
        callback_data=f"add_to_cart_{toy.id}"
    ))
    
    if is_favorite:
        builder.add(InlineKeyboardButton(
            text="❤️ Sevimlilarda",
            callback_data=f"remove_from_favorites_{toy.id}"
        ))
    else:
        builder.add(InlineKeyboardButton(
            text="❤️ Sevimlilarga qo'shish",
            callback_data=f"add_to_favorites_{toy.id}"
        ))
    
    # Buy button
    builder.add(InlineKeyboardButton(
        text="🛒 Buyurtma berish",
        callback_data=f"order_{toy.id}"
    ))
    
    toy_keyboard = builder.as_markup()
    
    # Check if toy has multiple media (new system)
    if db and bot:
        toy_media = MediaService.get_toy_media(db, toy.id)
        
        if toy_media and len(toy_media) > 0:
            # Use media group with caption on first media
            media_group = MediaService.get_media_for_media_group(
                toy_media,
                caption=message_text,
                parse_mode="HTML"
            )
            
            # Send media group with caption
            sent_messages = await bot.send_media_group(
                chat_id=message.chat.id,
                media=media_group
            )
            
            # Edit first message to add keyboard
            try:
                await bot.edit_message_reply_markup(
                    chat_id=message.chat.id,
                    message_id=sent_messages[0].message_id,
                    reply_markup=toy_keyboard
                )
            except Exception as e:
                # If editing fails, send keyboard as separate message
                logger.warning(f"Could not edit media group message: {e}")
                await bot.send_message(
                    chat_id=message.chat.id,
                    text="🔘",
                    reply_markup=toy_keyboard
                )
            return
    
    # Fallback to single media
    if toy.media_type == "image" and toy.media_file_id:
        await message.answer_photo(
            photo=toy.media_file_id,
            caption=message_text,
            parse_mode="HTML",
            reply_markup=toy_keyboard
        )
    elif toy.media_type == "video" and toy.media_file_id:
        await message.answer_video(
            video=toy.media_file_id,
            caption=message_text,
            parse_mode="HTML",
            reply_markup=toy_keyboard
        )
    else:
        await message.answer(
            message_text,
            parse_mode="HTML",
            reply_markup=toy_keyboard
        )


async def show_toy(message_or_callback, toy, category_id: int, page: int, total_pages: int, cat_id: int, db=None):
    """Display a toy with pagination - supports media groups"""
    from services.media_service import MediaService
    from aiogram.types import InputMediaPhoto, InputMediaVideo
    
    # Format message (will be sent after media group)
    category_name = toy.category.name if toy.category else "Kategoriyasiz"
    message_text = (
        f"📦 <b>{toy.title}</b>\n"
        f"🧸 Kategoriya: {category_name}\n\n"
        f"💰 Narxi: {toy.price}\n\n"
        f"📝 {toy.description}"
    )
    
    # Get user ID for favorites check
    user_id = None
    bot = None
    message = None
    
    if isinstance(message_or_callback, CallbackQuery):
        user_id = message_or_callback.from_user.id
        bot = message_or_callback.bot
        message = message_or_callback.message
    elif hasattr(message_or_callback, 'from_user'):
        user_id = message_or_callback.from_user.id
        bot = message_or_callback.bot
        message = message_or_callback
    else:
        # Fallback - get bot from context
        from aiogram import Bot
        try:
            bot = Bot.get_current()
        except:
            pass
        message = message_or_callback
    
    if user_id and db:
        is_favorite = FavoritesService.get_favorite(db, user_id, toy.id) is not None
    else:
        is_favorite = False
    
    # Build combined keyboard
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    
    builder = InlineKeyboardBuilder()
    
    # Pagination buttons
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(
            text="⬅️ Oldingi",
            callback_data=f"toy_page_{cat_id}_{page - 1}"
        ))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(
            text="Keyingi ➡️",
            callback_data=f"toy_page_{cat_id}_{page + 1}"
        ))
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    # Cart and favorites buttons
    builder.add(InlineKeyboardButton(
        text="➕ Savatchaga qo'shish",
        callback_data=f"add_to_cart_{toy.id}"
    ))
    
    if is_favorite:
        builder.add(InlineKeyboardButton(
            text="❤️ Sevimlilarda",
            callback_data=f"remove_from_favorites_{toy.id}"
        ))
    else:
        builder.add(InlineKeyboardButton(
            text="❤️ Sevimlilarga qo'shish",
            callback_data=f"add_to_favorites_{toy.id}"
        ))
    
    # Buy button
    builder.add(InlineKeyboardButton(
        text="🛒 Buyurtma berish",
        callback_data=f"order_{toy.id}"
    ))
    
    # Back button
    builder.add(InlineKeyboardButton(
        text="⬅️ Orqaga",
        callback_data=f"back_to_category_{cat_id}"
    ))
    
    combined_keyboard = builder.as_markup()
    
    # Check if toy has multiple media (new system)
    if db and bot:
        toy_media = MediaService.get_toy_media(db, toy.id)
        
        if toy_media and len(toy_media) > 0:
            # Use media group with caption on first media
            media_group = MediaService.get_media_for_media_group(
                toy_media,
                caption=message_text,
                parse_mode="HTML"
            )
            
            # Delete previous message if callback
            if isinstance(message_or_callback, CallbackQuery):
                try:
                    await message.delete()
                except:
                    pass
            
            # Send media group with caption
            sent_messages = await bot.send_media_group(
                chat_id=message.chat.id,
                media=media_group
            )
            
            # Edit first message to add keyboard
            # Telegram allows editing reply_markup on media group messages
            try:
                await bot.edit_message_reply_markup(
                    chat_id=message.chat.id,
                    message_id=sent_messages[0].message_id,
                    reply_markup=combined_keyboard
                )
            except Exception as e:
                # If editing fails (some Telegram clients don't support it),
                # send keyboard buttons as a separate message
                logger.warning(f"Could not edit media group message: {e}")
                await bot.send_message(
                    chat_id=message.chat.id,
                    text="🔘",
                    reply_markup=combined_keyboard
                )
            return
    
    # Fallback to old system (single media) for backward compatibility
    # Handle both Message and CallbackQuery
    if isinstance(message_or_callback, CallbackQuery):
        callback = message_or_callback
        
        # Delete previous message
        try:
            await message.delete()
        except:
            pass
        
        # Send new message
        if toy.media_type == "image" and toy.media_file_id:
            await callback.message.answer_photo(
                photo=toy.media_file_id,
                caption=message_text,
                parse_mode="HTML",
                reply_markup=combined_keyboard
            )
        elif toy.media_type == "video" and toy.media_file_id:
            await callback.message.answer_video(
                video=toy.media_file_id,
                caption=message_text,
                parse_mode="HTML",
                reply_markup=combined_keyboard
            )
        else:
            await callback.message.answer(
                message_text,
                parse_mode="HTML",
                reply_markup=combined_keyboard
            )
    else:
        # Regular message
        message = message_or_callback
        if toy.media_type == "image" and toy.media_file_id:
            await message.answer_photo(
                photo=toy.media_file_id,
                caption=message_text,
                parse_mode="HTML",
                reply_markup=combined_keyboard
            )
        elif toy.media_type == "video" and toy.media_file_id:
            await message.answer_video(
                video=toy.media_file_id,
                caption=message_text,
                parse_mode="HTML",
                reply_markup=combined_keyboard
            )
        else:
            await message.answer(
                message_text,
                parse_mode="HTML",
                reply_markup=combined_keyboard
            )




@router.callback_query(F.data.startswith("order_"))
async def handle_order(callback: CallbackQuery, state: FSMContext):
    """Handle order request"""
    try:
        toy_id = int(callback.data.split("_")[1])
        
        db = get_db_session()
        try:
            toy = CatalogService.get_toy_by_id(db, toy_id)
            if not toy or not toy.is_active:
                await callback.answer("❌ Bu o'yinchoq topilmadi", show_alert=True)
                return
            
            # Store toy info in state
            await state.update_data(toy_id=toy_id, toy_title=toy.title)
            await state.set_state(OrderStates.waiting_confirmation)
            
            order_text = (
                f"🛒 Buyurtma berish\n\n"
                f"📦 O'yinchoq: <b>{toy.title}</b>\n"
                f"💰 Narxi: {toy.price}\n\n"
                f"Buyurtmani tasdiqlaysizmi?"
            )
            
            await callback.message.edit_caption(
                caption=order_text,
                parse_mode="HTML",
                reply_markup=get_order_confirmation_keyboard(toy_id)
            )
            await callback.answer()
            
        finally:
            db.close()
            
    except (ValueError, IndexError) as e:
        logger.error(f"Error in handle_order: {e}")
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)


@router.callback_query(F.data.startswith("confirm_order_"))
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    """Confirm order and provide contact information"""
    try:
        toy_id = int(callback.data.split("_")[2])
        user_id = callback.from_user.id
        
        data = await state.get_data()
        toy_title = data.get("toy_title", "O'yinchoq")
        
        # Get contacts from database
        db = get_db_session()
        try:
            contacts = OrderContactService.get_active_contacts(db)
            contact_text = OrderContactService.format_contacts_for_display(contacts)
            
            # Get toy info for logging
            toy = CatalogService.get_toy_by_id(db, toy_id)
            if toy:
                category_id = toy.category_id if toy.category else None
                category_name = toy.category.name if toy.category else None
                
                # Log sale lead
                StatsService.log_sale_lead(
                    db=db,
                    user_id=user_id,
                    toy_id=toy_id,
                    toy_name=toy.title,
                    category_id=category_id,
                    category_name=category_name
                )
        finally:
            db.close()
        
        # Check if contacts are available
        if not contacts or contact_text == "❌ Hozircha buyurtma uchun kontaktlar mavjud emas":
            confirmation_text = (
                f"✅ <b>Buyurtma qabul qilindi!</b>\n\n"
                f"📦 O'yinchoq: <b>{toy_title}</b>\n\n"
                f"❌ Hozircha buyurtma uchun kontaktlar mavjud emas.\n\n"
                f"Tez orada siz bilan bog'lanamiz! 😊"
            )
        else:
            confirmation_text = (
                f"✅ <b>Buyurtma qabul qilindi!</b>\n\n"
                f"📦 O'yinchoq: <b>{toy_title}</b>\n\n"
                f"{contact_text}\n\n"
                f"Tez orada siz bilan bog'lanamiz! 😊"
            )
        
        await callback.message.edit_caption(
            caption=confirmation_text,
            parse_mode="HTML",
            reply_markup=None
        )
        
        await state.clear()
        await callback.answer("✅ Buyurtma qabul qilindi!")
        
    except Exception as e:
        logger.error(f"Error in confirm_order: {e}", exc_info=True)
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)


@router.callback_query(F.data.startswith("order_from_ad_"))
async def handle_order_from_ad(callback: CallbackQuery):
    """Handle order button from advertisement"""
    try:
        user_id = callback.from_user.id
        
        # Extract toy_id from callback data
        toy_id = int(callback.data.split("_")[-1])
        
        # Get contacts from database
        db = get_db_session()
        try:
            contacts = OrderContactService.get_active_contacts(db)
            contact_text = OrderContactService.format_contacts_for_display(contacts)
            
            # Get toy info for logging
            toy = CatalogService.get_toy_by_id(db, toy_id)
            if toy:
                category_id = toy.category_id if toy.category else None
                category_name = toy.category.name if toy.category else None
                
                # Log sale lead
                StatsService.log_sale_lead(
                    db=db,
                    user_id=user_id,
                    toy_id=toy_id,
                    toy_name=toy.title,
                    category_id=category_id,
                    category_name=category_name
                )
        finally:
            db.close()
        
        order_text = (
            f"🛒 <b>Buyurtma berish</b>\n\n"
            f"{contact_text}\n\n"
            f"Buyurtma berish uchun quyidagi kontaktlar bilan bog'laning."
        )
        
        await callback.message.answer(
            order_text,
            parse_mode="HTML"
        )
        await callback.answer("📞 Kontaktlar yuborildi")
        
    except (ValueError, IndexError) as e:
        logger.error(f"Error parsing order_from_ad callback: {e}", exc_info=True)
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
    except Exception as e:
        logger.error(f"Error in handle_order_from_ad: {e}", exc_info=True)
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)


@router.callback_query(F.data == "cancel_order")
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    """Cancel order"""
    await state.clear()
    await callback.answer("❌ Buyurtma bekor qilindi")
    # Show main menu
    await callback.message.answer(
        "🏠 Bosh menyu",
        reply_markup=get_main_menu_keyboard()
    )
