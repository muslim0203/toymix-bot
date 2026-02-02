"""
Admin handlers for managing toys and catalog
"""
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, PhotoSize, Video
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards.admin_kb import (
    get_admin_menu_keyboard,
    get_admin_categories_keyboard,
    get_admin_toy_pagination_keyboard,
    get_admin_toy_manage_keyboard,
    get_confirm_delete_keyboard,
    get_cancel_keyboard,
    get_media_done_keyboard
)
from keyboards.user_kb import get_main_menu_keyboard
from services.catalog_service import CatalogService
from services.category_service import CategoryService
from services.ads_scheduler import CategoryBasedAdScheduler
from database.db import get_db_session
from config import ADMIN_IDS

logger = logging.getLogger(__name__)
router = Router()


class AddToyStates(StatesGroup):
    """FSM states for adding a new toy"""
    waiting_media = State()  # First: collect media
    waiting_title = State()
    waiting_price = State()
    waiting_description = State()
    waiting_category = State()


class AddCategoryStates(StatesGroup):
    """FSM states for adding a category"""
    waiting_name = State()


class EditToyStates(StatesGroup):
    """FSM states for editing a toy"""
    waiting_field = State()
    waiting_new_value = State()


def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_IDS


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Handle /admin command"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return
    
    admin_text = (
        "👨‍💼 <b>Admin panel</b>\n\n"
        "Quyidagi funksiyalardan foydalaning:"
    )
    
    await message.answer(
        admin_text,
        parse_mode="HTML",
        reply_markup=get_admin_menu_keyboard()
    )


@router.message(F.text == "🏠 Admin menyu")
async def show_admin_menu(message: Message):
    """Show admin menu"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return
    
    admin_text = (
        "👨‍💼 <b>Admin panel</b>\n\n"
        "Quyidagi funksiyalardan foydalaning:"
    )
    
    await message.answer(
        admin_text,
        parse_mode="HTML",
        reply_markup=get_admin_menu_keyboard()
    )


@router.message(F.text == "➕ O'yinchoq qo'shish")
async def start_add_toy(message: Message, state: FSMContext):
    """Start adding a new toy - first collect media"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return
    
    # Initialize media list in state
    await state.update_data(media_list=[])
    await state.set_state(AddToyStates.waiting_media)
    await message.answer(
        "➕ <b>Yangi o'yinchoq qo'shish</b>\n\n"
        "📷 Rasm yoki videolarni yuboring (bir nechta bo'lishi mumkin).\n\n"
        "Tugatgach <b>✅ Tugatish</b> tugmasini bosing.",
        parse_mode="HTML",
        reply_markup=get_media_done_keyboard()
    )


@router.message(AddToyStates.waiting_title)
async def process_title(message: Message, state: FSMContext):
    """Process toy title"""
    await state.update_data(title=message.text)
    await state.set_state(AddToyStates.waiting_price)
    await message.answer(
        "💰 Narxni yuboring (masalan: 50000 so'm):",
        reply_markup=get_cancel_keyboard()
    )


@router.message(AddToyStates.waiting_price)
async def process_price(message: Message, state: FSMContext):
    """Process toy price"""
    await state.update_data(price=message.text)
    await state.set_state(AddToyStates.waiting_description)
    await message.answer(
        "📝 Tavsifni yuboring:",
        reply_markup=get_cancel_keyboard()
    )


@router.message(AddToyStates.waiting_description)
async def process_description(message: Message, state: FSMContext):
    """Process toy description"""
    await state.update_data(description=message.text)
    await state.set_state(AddToyStates.waiting_category)
    
    db = get_db_session()
    try:
        categories = CategoryService.get_active_categories(db)
        if categories:
            await message.answer(
                "📂 Kategoriyani tanlang yoki 'Kategoriyasiz' yozing:",
                reply_markup=get_admin_categories_keyboard(categories)
            )
        else:
            await message.answer(
                "📂 Kategoriya nomini yuboring yoki 'Kategoriyasiz' yozing:",
                reply_markup=get_cancel_keyboard()
            )
    finally:
        db.close()


@router.message(AddToyStates.waiting_category)
async def process_category(message: Message, state: FSMContext):
    """Process toy category and save toy"""
    # Check for cancel
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi", reply_markup=get_admin_menu_keyboard())
        return
    
    category_name = message.text.replace("✅ ", "").replace("❌ ", "").strip()
    
    category_id = None
    if category_name.lower() != "kategoriyasiz":
        db = get_db_session()
        try:
            category = CategoryService.get_category_by_name(db, category_name)
            if category:
                category_id = category.id
            else:
                await message.answer(
                    "❌ Kategoriya topilmadi. 'Kategoriyasiz' yozing yoki mavjud kategoriyani tanlang:",
                    reply_markup=get_cancel_keyboard()
                )
                return
        finally:
            db.close()
    
    # Get all data from state
    data = await state.get_data()
    title = data.get("title")
    price = data.get("price")
    description = data.get("description")
    media_list = data.get("media_list", [])
    
    if not media_list:
        await message.answer(
            "❌ Kamida bitta rasm yoki video yuboring.\n\n"
            "Media yuborib, keyin <code>/done</code> yozing.",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(AddToyStates.waiting_media)
        return
    
    # Create toy
    db = get_db_session()
    try:
        from services.media_service import MediaService
        
        # Create toy (with backward compatibility fields)
        toy = CatalogService.create_toy(
            db,
            title=title,
            price=price,
            description=description,
            category_id=category_id,
            media_type="image" if media_list[0][1] == "photo" else "video",  # For backward compatibility
            media_file_id=media_list[0][0]  # For backward compatibility
        )
        
        # Add all media
        MediaService.add_multiple_media(db, toy.id, media_list)
        
        await message.answer(
            f"✅ O'yinchoq muvaffaqiyatli qo'shildi!\n\n"
            f"📦 {toy.title}\n"
            f"💰 {toy.price}\n"
            f"📷 {len(media_list)} ta media",
            reply_markup=get_admin_menu_keyboard()
        )
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error creating toy: {e}", exc_info=True)
        await message.answer(
            "❌ Xatolik yuz berdi. Qayta urinib ko'ring.",
            reply_markup=get_admin_menu_keyboard()
        )
        await state.clear()
    finally:
        db.close()


@router.message(AddToyStates.waiting_media, F.photo)
async def process_photo(message: Message, state: FSMContext, bot: Bot):
    """Process photo media (including forwarded) - add to media list"""
    try:
        # Handle both direct and forwarded photos
        if message.photo:
            photo: PhotoSize = message.photo[-1]  # Get highest resolution
            file_id = photo.file_id
        elif message.document and message.document.mime_type and message.document.mime_type.startswith('image/'):
            # Handle forwarded images as documents
            file_id = message.document.file_id
        else:
            await message.answer(
                "❌ Rasm topilmadi. Iltimos, rasm yoki video yuboring.",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        # Get current media list from state
        data = await state.get_data()
        media_list = data.get("media_list", [])
        
        # Add photo to list
        media_list.append((file_id, "photo"))
        await state.update_data(media_list=media_list)
        
        await message.answer(
            f"✅ Rasm qo'shildi! ({len(media_list)} ta media)\n\n"
            "Yana rasm/video yuborishingiz mumkin yoki <b>✅ Tugatish</b> tugmasini bosing.",
            parse_mode="HTML",
            reply_markup=get_media_done_keyboard()
        )
            
    except Exception as e:
        logger.error(f"Error processing photo: {e}", exc_info=True)
        await message.answer(
            "❌ Rasmni qayta ishlashda xatolik yuz berdi.\n\n"
            "Iltimos, boshqa rasm yuboring.",
            reply_markup=get_cancel_keyboard()
        )


@router.message(AddToyStates.waiting_media, F.video)
async def process_video(message: Message, state: FSMContext):
    """Process video media (including forwarded) - add to media list"""
    try:
        # Handle both direct and forwarded videos
        if message.video:
            video: Video = message.video
            file_id = video.file_id
        elif message.document and message.document.mime_type and message.document.mime_type.startswith('video/'):
            # Handle forwarded videos as documents
            file_id = message.document.file_id
        else:
            await message.answer(
                "❌ Video topilmadi. Iltimos, rasm yoki video yuboring.",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        # Get current media list from state
        data = await state.get_data()
        media_list = data.get("media_list", [])
        
        # Add video to list
        media_list.append((file_id, "video"))
        await state.update_data(media_list=media_list)
        
        await message.answer(
            f"✅ Video qo'shildi! ({len(media_list)} ta media)\n\n"
            "Yana rasm/video yuborishingiz mumkin yoki <b>✅ Tugatish</b> tugmasini bosing.",
            parse_mode="HTML",
            reply_markup=get_media_done_keyboard()
        )
            
    except Exception as e:
        logger.error(f"Error processing video: {e}", exc_info=True)
        await message.answer(
            "❌ Videoni qayta ishlashda xatolik yuz berdi.\n\n"
            "Iltimos, boshqa video yuboring.",
            reply_markup=get_cancel_keyboard()
        )


@router.message(AddToyStates.waiting_media, F.document)
async def process_document_media(message: Message, state: FSMContext):
    """Process media sent as document (including forwarded) - add to media list"""
    try:
        if not message.document:
            await message.answer(
                "❌ Fayl topilmadi. Iltimos, rasm yoki video yuboring.",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        mime_type = message.document.mime_type or ""
        file_id = message.document.file_id
        
        # Determine media type
        if mime_type.startswith('image/'):
            media_type = "photo"
        elif mime_type.startswith('video/'):
            media_type = "video"
        else:
            await message.answer(
                "❌ Bu fayl rasm yoki video emas.\n\n"
                "Iltimos, rasm yoki video fayl yuboring.",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        # Get current media list from state
        data = await state.get_data()
        media_list = data.get("media_list", [])
        
        # Add media to list
        media_list.append((file_id, media_type))
        await state.update_data(media_list=media_list)
        
        await message.answer(
            f"✅ {media_type.capitalize()} qo'shildi! ({len(media_list)} ta media)\n\n"
            "Yana rasm/video yuborishingiz mumkin yoki <b>✅ Tugatish</b> tugmasini bosing.",
            parse_mode="HTML",
            reply_markup=get_media_done_keyboard()
        )
            
    except Exception as e:
        logger.error(f"Error processing document media: {e}", exc_info=True)
        await message.answer(
            "❌ Faylni qayta ishlashda xatolik yuz berdi.\n\n"
            "Iltimos, boshqa fayl yuboring.",
            reply_markup=get_cancel_keyboard()
        )


@router.message(AddToyStates.waiting_media, F.text == "✅ Tugatish")
async def finish_media_collection(message: Message, state: FSMContext):
    """Finish media collection and proceed to title"""
    data = await state.get_data()
    media_list = data.get("media_list", [])
    
    if not media_list:
        await message.answer(
            "❌ Kamida bitta rasm yoki video yuboring.\n\n"
            "Media yuborib, keyin <b>✅ Tugatish</b> tugmasini bosing.",
            parse_mode="HTML",
            reply_markup=get_media_done_keyboard()
        )
        return
    
    await state.set_state(AddToyStates.waiting_title)
    await message.answer(
        f"✅ {len(media_list)} ta media qabul qilindi!\n\n"
        "O'yinchoq nomini kiriting:",
        reply_markup=get_cancel_keyboard()
    )


@router.message(AddToyStates.waiting_media, Command("done"))
async def finish_media_collection_command(message: Message, state: FSMContext):
    """Finish media collection via /done command (backward compatibility)"""
    await finish_media_collection(message, state)


@router.message(AddToyStates.waiting_media)
async def process_invalid_media(message: Message, state: FSMContext):
    """Handle invalid media input (not photo or video)"""
    # Check for cancel
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer(
            "❌ Bekor qilindi",
            reply_markup=get_admin_menu_keyboard()
        )
        return
    
    # Check for done button (already handled by F.text filter, but just in case)
    if message.text == "✅ Tugatish":
        await finish_media_collection(message, state)
        return
    
    # Check for /done command (backward compatibility)
    if message.text and message.text.strip() == "/done":
        await finish_media_collection(message, state)
        return
    
    await message.answer(
        "❌ Iltimos, rasm yoki video yuboring!\n\n"
        "Telegram orqali rasm yoki video fayl yuboring (forward qilingan ham bo'lishi mumkin).\n"
        "Tugatgach <b>✅ Tugatish</b> tugmasini bosing.",
        parse_mode="HTML",
        reply_markup=get_media_done_keyboard()
    )


@router.message(F.text == "📂 Kategoriya qo'shish")
async def start_add_category(message: Message, state: FSMContext):
    """Start adding a new category"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return
    
    await state.set_state(AddCategoryStates.waiting_name)
    await message.answer(
        "📂 <b>Yangi kategoriya qo'shish</b>\n\n"
        "Kategoriya nomini yuboring:",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )


@router.message(AddCategoryStates.waiting_name)
async def process_category_name(message: Message, state: FSMContext):
    """Process category name"""
    # Check for cancel
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer(
            "❌ Bekor qilindi",
            reply_markup=get_admin_menu_keyboard()
        )
        return
    
    category_name = message.text.strip()
    
    # Validate: empty name
    if not category_name:
        await message.answer(
            "❌ Kategoriya nomi bo'sh bo'lishi mumkin emas.\n\n"
            "Kategoriya nomini kiriting:",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    # Validate: name too long
    if len(category_name) > 100:
        await message.answer(
            "❌ Kategoriya nomi juda uzun (maksimum 100 belgi).\n\n"
            "Qisqa kategoriya nomini kiriting:",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    db = get_db_session()
    try:
        # Check if category already exists
        existing = CategoryService.get_category_by_name(db, category_name)
        if existing:
            await message.answer(
                f"❌ '{category_name}' kategoriyasi allaqachon mavjud.\n\n"
                "Boshqa nom kiriting:",
                reply_markup=get_cancel_keyboard()
            )
            return  # Don't clear state, let user try again
        
        # Create category
        category = CategoryService.create_category(db, category_name)
        await message.answer(
            f"✅ Kategoriya muvaffaqiyatli qo'shildi!\n\n"
            f"📂 {category.name}",
            reply_markup=get_admin_menu_keyboard()
        )
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error creating category: {e}", exc_info=True)
        await message.answer(
            "❌ Xatolik yuz berdi. Qayta urinib ko'ring.",
            reply_markup=get_admin_menu_keyboard()
        )
        await state.clear()
    finally:
        db.close()


@router.message(F.text == "📦 Katalogni ko'rish")
async def admin_view_catalog(message: Message):
    """Show admin catalog view - categories"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return
    
    db = get_db_session()
    try:
        categories = CategoryService.get_all_categories(db)
        
        if not categories:
            await message.answer(
                "😔 Katalogda kategoriyalar yo'q.\n\n"
                "Yangi kategoriya qo'shing!",
                reply_markup=get_admin_menu_keyboard()
            )
            return
        
        categories_text = "📂 Kategoriyalarni tanlang:"
        await message.answer(
            categories_text,
            reply_markup=get_admin_categories_keyboard(categories)
        )
        
    except Exception as e:
        logger.error(f"Error showing admin catalog: {e}", exc_info=True)
        await message.answer(
            "❌ Xatolik yuz berdi.",
            reply_markup=get_admin_menu_keyboard()
        )
    finally:
        db.close()


@router.message(F.text.startswith("✅ ") | F.text.startswith("❌ "))
async def admin_view_category_toys(message: Message):
    """Show toys in selected category (admin)"""
    category_name = message.text.replace("✅ ", "").replace("❌ ", "").strip()
    
    db = get_db_session()
    try:
        category = CategoryService.get_category_by_name(db, category_name)
        
        if not category:
            await message.answer(
                "❌ Kategoriya topilmadi.",
                reply_markup=get_admin_menu_keyboard()
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
                f"😔 '{category.name}' kategoriyasida o'yinchoqlar yo'q.",
                reply_markup=get_admin_categories_keyboard(CategoryService.get_all_categories(db))
            )
            return
        
        # Show first toy
        toy = toys[0]
        await show_admin_toy(message, toy, category.id, 1, total_pages, category.id)
        
    except Exception as e:
        logger.error(f"Error showing admin category toys: {e}", exc_info=True)
        await message.answer(
            "❌ Xatolik yuz berdi.",
            reply_markup=get_admin_menu_keyboard()
        )
    finally:
        db.close()


async def show_admin_toy(message_or_callback, toy, category_id: int, page: int, total_pages: int, cat_id: int = None):
    """Display a toy with pagination (admin view)"""
    status_emoji = "✅" if toy.is_active else "❌"
    message_text = (
        f"{status_emoji} <b>{toy.title}</b>\n\n"
        f"💰 Narxi: {toy.price}\n\n"
        f"{toy.description}\n\n"
        f"📄 {page}/{total_pages}\n"
        f"🆔 ID: {toy.id}"
    )
    
    if isinstance(message_or_callback, CallbackQuery):
        callback = message_or_callback
        message = callback.message
        
        try:
            await message.delete()
        except:
            pass
        
        if toy.media_type == "image":
            await callback.message.answer_photo(
                photo=toy.media_file_id,
                caption=message_text,
                parse_mode="HTML",
                reply_markup=get_admin_toy_pagination_keyboard(page, total_pages, toy.id, cat_id)
            )
        elif toy.media_type == "video":
            await callback.message.answer_video(
                video=toy.media_file_id,
                caption=message_text,
                parse_mode="HTML",
                reply_markup=get_admin_toy_pagination_keyboard(page, total_pages, toy.id, cat_id)
            )
    else:
        message = message_or_callback
        if toy.media_type == "image":
            await message.answer_photo(
                photo=toy.media_file_id,
                caption=message_text,
                parse_mode="HTML",
                reply_markup=get_admin_toy_pagination_keyboard(page, total_pages, toy.id, cat_id)
            )
        elif toy.media_type == "video":
            await message.answer_video(
                video=toy.media_file_id,
                caption=message_text,
                parse_mode="HTML",
                reply_markup=get_admin_toy_pagination_keyboard(page, total_pages, toy.id, cat_id)
            )


@router.callback_query(F.data.startswith("admin_toy_page_"))
async def handle_admin_toy_pagination(callback: CallbackQuery):
    """Handle admin toy pagination"""
    try:
        # Format: admin_toy_page_{category_id}_{page} or admin_toy_page_all_{page}
        parts = callback.data.split("_")
        category_part = parts[3]
        page = int(parts[4])
        
        db = get_db_session()
        try:
            if category_part == "all":
                # Show all toys
                toys, total_pages = CatalogService.get_all_toys(db, page=page)
                category_id = None
            else:
                category_id = int(category_part)
                category = CategoryService.get_category_by_id(db, category_id)
                if not category:
                    await callback.answer("❌ Kategoriya topilmadi", show_alert=True)
                    return
                
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
            await show_admin_toy(callback, toy, category_id or 0, page, total_pages, category_id)
            await callback.answer()
            
        finally:
            db.close()
            
    except (ValueError, IndexError) as e:
        logger.error(f"Error in admin pagination: {e}", exc_info=True)
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)


@router.callback_query(F.data.startswith("admin_manage_"))
async def manage_toy(callback: CallbackQuery):
    """Show toy management options"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqi yo'q", show_alert=True)
        return
    
    try:
        toy_id = int(callback.data.split("_")[2])
        
        db = get_db_session()
        try:
            toy = CatalogService.get_toy_by_id(db, toy_id)
            if not toy:
                await callback.answer("❌ O'yinchoq topilmadi", show_alert=True)
                return
            
            status_text = "Faol ✅" if toy.is_active else "Nofaol ❌"
            message_text = (
                f"⚙️ <b>O'yinchoqni boshqarish</b>\n\n"
                f"📦 {toy.title}\n"
                f"💰 {toy.price}\n"
                f"📊 Holati: {status_text}\n"
                f"🆔 ID: {toy.id}"
            )
            
            await callback.message.edit_caption(
                caption=message_text,
                parse_mode="HTML",
                reply_markup=get_admin_toy_manage_keyboard(toy.id, toy.is_active)
            )
            await callback.answer()
            
        finally:
            db.close()
            
    except (ValueError, IndexError) as e:
        logger.error(f"Error in manage_toy: {e}")
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)


@router.callback_query(F.data.startswith("admin_toggle_"))
async def toggle_toy(callback: CallbackQuery):
    """Toggle toy active status"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqi yo'q", show_alert=True)
        return
    
    try:
        toy_id = int(callback.data.split("_")[2])
        
        db = get_db_session()
        try:
            toy = CatalogService.toggle_toy_active(db, toy_id)
            if not toy:
                await callback.answer("❌ O'yinchoq topilmadi", show_alert=True)
                return
            
            status_text = "Faol ✅" if toy.is_active else "Nofaol ❌"
            message_text = (
                f"⚙️ <b>O'yinchoqni boshqarish</b>\n\n"
                f"📦 {toy.title}\n"
                f"💰 {toy.price}\n"
                f"📊 Holati: {status_text}\n"
                f"🆔 ID: {toy.id}"
            )
            
            await callback.message.edit_caption(
                caption=message_text,
                parse_mode="HTML",
                reply_markup=get_admin_toy_manage_keyboard(toy.id, toy.is_active)
            )
            await callback.answer(f"✅ Holat o'zgartirildi: {status_text}")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in toggle_toy: {e}", exc_info=True)
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)


@router.callback_query(F.data.startswith("admin_delete_"))
async def confirm_delete_toy(callback: CallbackQuery):
    """Show delete confirmation"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqi yo'q", show_alert=True)
        return
    
    try:
        toy_id = int(callback.data.split("_")[2])
        
        db = get_db_session()
        try:
            toy = CatalogService.get_toy_by_id(db, toy_id)
            if not toy:
                await callback.answer("❌ O'yinchoq topilmadi", show_alert=True)
                return
            
            message_text = (
                f"⚠️ <b>O'yinchoqni o'chirish</b>\n\n"
                f"📦 {toy.title}\n\n"
                f"Rostdan ham o'chirmoqchimisiz?"
            )
            
            await callback.message.edit_caption(
                caption=message_text,
                parse_mode="HTML",
                reply_markup=get_confirm_delete_keyboard(toy_id)
            )
            await callback.answer()
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in confirm_delete_toy: {e}", exc_info=True)
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)


@router.callback_query(F.data.startswith("admin_edit_"))
async def start_edit_toy(callback: CallbackQuery, state: FSMContext):
    """Start editing a toy"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqi yo'q", show_alert=True)
        return
    
    try:
        toy_id = int(callback.data.split("_")[2])
        
        db = get_db_session()
        try:
            toy = CatalogService.get_toy_by_id(db, toy_id)
            if not toy:
                await callback.answer("❌ O'yinchoq topilmadi", show_alert=True)
                return
            
            # Store toy_id in state
            await state.update_data(toy_id=toy_id)
            
            # Show edit options
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            
            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(
                text="📝 Nom",
                callback_data=f"edit_field_{toy_id}_title"
            ))
            builder.add(InlineKeyboardButton(
                text="💰 Narx",
                callback_data=f"edit_field_{toy_id}_price"
            ))
            builder.add(InlineKeyboardButton(
                text="📄 Tavsif",
                callback_data=f"edit_field_{toy_id}_description"
            ))
            builder.add(InlineKeyboardButton(
                text="📂 Kategoriya",
                callback_data=f"edit_field_{toy_id}_category"
            ))
            builder.add(InlineKeyboardButton(
                text="🖼️ Media",
                callback_data=f"edit_field_{toy_id}_media"
            ))
            builder.add(InlineKeyboardButton(
                text="⬅️ Orqaga",
                callback_data=f"admin_manage_{toy_id}"
            ))
            builder.adjust(2)
            
            message_text = (
                f"✏️ <b>O'yinchoqni tahrirlash</b>\n\n"
                f"📦 {toy.title}\n"
                f"💰 {toy.price}\n\n"
                f"Tahrirlash uchun maydonni tanlang:"
            )
            
            await callback.message.edit_caption(
                caption=message_text,
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )
            await callback.answer()
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in start_edit_toy: {e}", exc_info=True)
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)


@router.callback_query(F.data.startswith("edit_field_"))
async def select_edit_field(callback: CallbackQuery, state: FSMContext):
    """Select field to edit"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqi yo'q", show_alert=True)
        return
    
    try:
        parts = callback.data.split("_")
        toy_id = int(parts[2])
        field = parts[3]
        
        await state.update_data(toy_id=toy_id, field=field)
        await state.set_state(EditToyStates.waiting_new_value)
        
        db = get_db_session()
        try:
            toy = CatalogService.get_toy_by_id(db, toy_id)
            if not toy:
                await callback.answer("❌ O'yinchoq topilmadi", show_alert=True)
                return
            
            field_names = {
                "title": "Nom",
                "price": "Narx",
                "description": "Tavsif",
                "category": "Kategoriya",
                "media": "Media (rasm/video)"
            }
            
            if field == "category":
                # Show category selection
                categories = CategoryService.get_active_categories(db)
                if not categories:
                    await callback.answer("❌ Kategoriya mavjud emas", show_alert=True)
                    return
                
                from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                from aiogram.utils.keyboard import InlineKeyboardBuilder
                
                builder = InlineKeyboardBuilder()
                for category in categories:
                    builder.add(InlineKeyboardButton(
                        text=f"📂 {category.name}",
                        callback_data=f"edit_category_{toy_id}_{category.id}"
                    ))
                builder.add(InlineKeyboardButton(
                    text="⬅️ Orqaga",
                    callback_data=f"admin_edit_{toy_id}"
                ))
                builder.adjust(1)
                
                await callback.message.edit_caption(
                    caption=f"📂 Kategoriyani tanlang:",
                    parse_mode="HTML",
                    reply_markup=builder.as_markup()
                )
                await callback.answer()
            elif field == "media":
                from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                from aiogram.utils.keyboard import InlineKeyboardBuilder
                
                builder = InlineKeyboardBuilder()
                builder.add(InlineKeyboardButton(
                    text="⬅️ Orqaga",
                    callback_data=f"admin_edit_{toy_id}"
                ))
                
                await callback.message.edit_caption(
                    caption=f"🖼️ Yangi rasm yoki video yuboring:",
                    parse_mode="HTML",
                    reply_markup=builder.as_markup()
                )
                await callback.answer()
            else:
                from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                from aiogram.utils.keyboard import InlineKeyboardBuilder
                
                builder = InlineKeyboardBuilder()
                builder.add(InlineKeyboardButton(
                    text="⬅️ Orqaga",
                    callback_data=f"admin_edit_{toy_id}"
                ))
                
                current_value = getattr(toy, field, "")
                await callback.message.edit_caption(
                    caption=f"✏️ Yangi {field_names.get(field, field)} kiriting:\n\n"
                           f"Joriy qiymat: {current_value}",
                    parse_mode="HTML",
                    reply_markup=builder.as_markup()
                )
                await callback.answer()
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in select_edit_field: {e}", exc_info=True)
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)


@router.callback_query(F.data.startswith("edit_category_"))
async def edit_toy_category(callback: CallbackQuery, state: FSMContext):
    """Edit toy category"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqi yo'q", show_alert=True)
        return
    
    try:
        parts = callback.data.split("_")
        toy_id = int(parts[2])
        category_id = int(parts[3])
        
        db = get_db_session()
        try:
            toy = CatalogService.get_toy_by_id(db, toy_id)
            category = CategoryService.get_category_by_id(db, category_id)
            
            if not toy or not category:
                await callback.answer("❌ Xatolik", show_alert=True)
                return
            
            # Update category
            toy.category_id = category_id
            db.commit()
            
            await callback.message.edit_caption(
                caption=f"✅ Kategoriya yangilandi: {category.name}",
                parse_mode="HTML",
                reply_markup=get_admin_toy_manage_keyboard(toy.id, toy.is_active)
            )
            await callback.answer("✅ Yangilandi")
            await state.clear()
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in edit_toy_category: {e}", exc_info=True)
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)


@router.message(EditToyStates.waiting_new_value)
async def process_edit_value(message: Message, state: FSMContext):
    """Process new value for toy field"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        await state.clear()
        return
    
    # Get data before clearing state
    data = await state.get_data()
    toy_id = data.get("toy_id")
    field = data.get("field")
    
    # Check for cancel (if sent as text)
    if message.text and "bekor" in message.text.lower():
        await state.clear()
        await message.answer(
            "❌ Bekor qilindi",
            reply_markup=get_admin_menu_keyboard()
        )
        return
    
    if not toy_id or not field:
        await message.answer("❌ Xatolik", reply_markup=get_admin_menu_keyboard())
        await state.clear()
        return
    
    data = await state.get_data()
    toy_id = data.get("toy_id")
    field = data.get("field")
    
    if not toy_id or not field:
        await message.answer("❌ Xatolik", reply_markup=get_admin_menu_keyboard())
        await state.clear()
        return
    
    db = get_db_session()
    try:
        toy = CatalogService.get_toy_by_id(db, toy_id)
        if not toy:
            await message.answer("❌ O'yinchoq topilmadi", reply_markup=get_admin_menu_keyboard())
            await state.clear()
            return
        
        if field == "title":
            if not message.text or len(message.text.strip()) == 0:
                await message.answer("❌ Nom bo'sh bo'lishi mumkin emas.")
                return
            toy.title = message.text.strip()
        elif field == "price":
            if not message.text or len(message.text.strip()) == 0:
                await message.answer("❌ Narx bo'sh bo'lishi mumkin emas.")
                return
            toy.price = message.text.strip()
        elif field == "description":
            if not message.text or len(message.text.strip()) == 0:
                await message.answer("❌ Tavsif bo'sh bo'lishi mumkin emas.")
                return
            toy.description = message.text.strip()
        elif field == "media":
            # Handle media update
            if message.photo:
                file_id = message.photo[-1].file_id
                toy.media_type = "image"
                toy.media_file_id = file_id
            elif message.video:
                file_id = message.video.file_id
                toy.media_type = "video"
                toy.media_file_id = file_id
            elif message.document:
                mime_type = message.document.mime_type or ""
                if mime_type.startswith("video/"):
                    file_id = message.document.file_id
                    toy.media_type = "video"
                    toy.media_file_id = file_id
                else:
                    await message.answer("❌ Faqat rasm yoki video qabul qilinadi.")
                    return
            else:
                await message.answer("❌ Rasm yoki video yuboring.")
                return
        
        db.commit()
        
        await message.answer(
            f"✅ O'yinchoq yangilandi!",
            reply_markup=get_admin_menu_keyboard()
        )
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error in process_edit_value: {e}", exc_info=True)
        await message.answer("❌ Xatolik yuz berdi", reply_markup=get_admin_menu_keyboard())
        await state.clear()
    finally:
        db.close()


@router.callback_query(F.data.startswith("admin_confirm_delete_"))
async def delete_toy(callback: CallbackQuery):
    """Delete toy"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqi yo'q", show_alert=True)
        return
    
    try:
        toy_id = int(callback.data.split("_")[3])
        
        db = get_db_session()
        try:
            toy = CatalogService.get_toy_by_id(db, toy_id)
            if not toy:
                await callback.answer("❌ O'yinchoq topilmadi", show_alert=True)
                return
            
            toy_title = toy.title
            success = CatalogService.delete_toy(db, toy_id)
            
            if success:
                await callback.message.edit_text(
                    f"✅ O'yinchoq o'chirildi: {toy_title}",
                    reply_markup=get_admin_menu_keyboard()
                )
                await callback.answer("✅ O'chirildi")
            else:
                await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in delete_toy: {e}", exc_info=True)
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)


@router.message(F.text == "📊 Statistika")
async def show_stats(message: Message):
    """Show catalog statistics"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return
    
    db = get_db_session()
    try:
        toy_stats = CatalogService.get_stats(db)
        category_stats = CategoryService.get_category_stats(db)
        
        stats_text = (
            "📊 <b>Katalog statistikasi</b>\n\n"
            f"<b>O'yinchoqlar:</b>\n"
            f"📦 Jami: {toy_stats['total']}\n"
            f"✅ Faol: {toy_stats['active']}\n"
            f"❌ Nofaol: {toy_stats['inactive']}\n\n"
            f"<b>Kategoriyalar:</b>\n"
            f"📂 Jami: {category_stats['total']}\n"
            f"✅ Faol: {category_stats['active']}\n"
            f"❌ Nofaol: {category_stats['inactive']}"
        )
        
        await message.answer(
            stats_text,
            parse_mode="HTML",
            reply_markup=get_admin_menu_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error showing stats: {e}", exc_info=True)
        await message.answer(
            "❌ Xatolik yuz berdi.",
            reply_markup=get_admin_menu_keyboard()
        )
    finally:
        db.close()


@router.message(F.text == "📣 Reklama yuborish")
async def send_manual_ad(message: Message, bot: Bot):
    """Manually trigger advertisement"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return
    
    await message.answer("📢 Reklama yuborilmoqda...", reply_markup=get_admin_menu_keyboard())
    
    scheduler = CategoryBasedAdScheduler(bot)
    success = await scheduler.post_manual_ad()
    
    if success:
        await message.answer(
            "✅ Reklama muvaffaqiyatli yuborildi!",
            reply_markup=get_admin_menu_keyboard()
        )
    else:
        await message.answer(
            "❌ Reklama yuborishda xatolik yuz berdi.",
            reply_markup=get_admin_menu_keyboard()
        )


@router.message(F.text == "❌ Bekor qilish")
async def cancel_admin_action(message: Message, state: FSMContext):
    """Cancel admin action"""
    await state.clear()
    await message.answer(
        "❌ Bekor qilindi",
        reply_markup=get_admin_menu_keyboard()
    )


@router.message(F.text == "⬅️ Orqaga")
async def admin_go_back(message: Message):
    """Go back to admin catalog"""
    await admin_view_catalog(message)


@router.message(F.text == "🏠 Bosh menyu")
async def go_to_main_menu(message: Message):
    """Go to main menu"""
    if is_admin(message.from_user.id):
        await show_admin_menu(message)
    else:
        await message.answer(
            "👋 Bosh menyu",
            reply_markup=get_main_menu_keyboard()
        )
