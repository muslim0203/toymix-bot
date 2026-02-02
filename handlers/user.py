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
    """Show toys in selected category"""
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
        
        # Get toys for this category (page 1)
        toys, total_pages = CatalogService.get_active_toys_by_category(
            db, 
            category_id=category.id, 
            page=1
        )
        
        if not toys:
            await message.answer(
                f"😔 '{category.name}' kategoriyasida hozircha o'yinchoqlar yo'q.",
                reply_markup=get_categories_keyboard(CategoryService.get_active_categories(db))
            )
            return
        
        # Show first toy
        toy = toys[0]
        await show_toy(message, toy, category.id, 1, total_pages, category.id, db=db)
        
    except Exception as e:
        logger.error(f"Error showing category toys: {e}", exc_info=True)
        await message.answer(
            "❌ Xatolik yuz berdi.",
            reply_markup=get_main_menu_keyboard()
        )
    finally:
        db.close()


@router.callback_query(F.data.startswith("toy_page_"))
async def handle_toy_pagination(callback: CallbackQuery):
    """Handle toy pagination"""
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
            
            # Get toys for this category and page
            toys, total_pages = CatalogService.get_active_toys_by_category(
                db, 
                category_id=category_id, 
                page=page
            )
            
            if not toys:
                await callback.answer("❌ O'yinchoqlar topilmadi", show_alert=True)
                return
            
            # Show toy at current page
            toy = toys[0]
            await show_toy(callback, toy, category_id, page, total_pages, category_id, db=db)
            await callback.answer()
            
        finally:
            db.close()
            
    except (ValueError, IndexError) as e:
        logger.error(f"Error in pagination: {e}", exc_info=True)
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)


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
