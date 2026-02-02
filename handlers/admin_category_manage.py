"""
Admin handlers for category management (edit and delete)
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from keyboards.admin_kb import get_admin_menu_keyboard
from keyboards.category_manage_kb import (
    get_category_list_keyboard,
    get_confirm_delete_category_keyboard,
    get_cancel_keyboard
)
from services.category_service import CategoryService
from services.catalog_service import CatalogService
from database.db import get_db_session
from config import ADMIN_IDS
from states.category_manage_states import EditCategoryStates, DeleteCategoryStates

logger = logging.getLogger(__name__)
router = Router()


def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_IDS


@router.message(F.text == "✏️ Kategoriyalarni tahrirlash")
async def start_edit_categories(message: Message, state: FSMContext):
    """Start category editing flow"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return
    
    db = get_db_session()
    try:
        categories = CategoryService.get_active_categories(db)
        
        if not categories:
            await message.answer(
                "❌ Tahrirlash uchun kategoriya mavjud emas.\n\n"
                "Avval kategoriya qo'shing.",
                reply_markup=get_admin_menu_keyboard()
            )
            return
        
        await state.set_state(EditCategoryStates.waiting_category_selection)
        await message.answer(
            "✏️ <b>Kategoriyani tahrirlash</b>\n\n"
            "Tahrirlash uchun kategoriyani tanlang:",
            parse_mode="HTML",
            reply_markup=get_category_list_keyboard(categories)
        )
        
    except Exception as e:
        logger.error(f"Error starting edit categories: {e}", exc_info=True)
        await message.answer(
            "❌ Xatolik yuz berdi.",
            reply_markup=get_admin_menu_keyboard()
        )
    finally:
        db.close()


@router.message(EditCategoryStates.waiting_category_selection, F.text.startswith("🧸 "))
async def select_category_to_edit(message: Message, state: FSMContext):
    """Select category to edit"""
    # Check for cancel/back
    if message.text == "❌ Bekor qilish" or message.text == "⬅️ Orqaga" or message.text == "🏠 Admin menyu":
        await state.clear()
        if message.text == "🏠 Admin menyu":
            await message.answer(
                "🏠 Admin menyu",
                reply_markup=get_admin_menu_keyboard()
            )
        else:
            await message.answer(
                "❌ Bekor qilindi",
                reply_markup=get_admin_menu_keyboard()
            )
        return
    
    category_name = message.text.replace("🧸 ", "").strip()
    
    db = get_db_session()
    try:
        category = CategoryService.get_category_by_name(db, category_name)
        
        if not category:
            await message.answer(
                "❌ Kategoriya topilmadi.\n\n"
                "Kategoriyani qayta tanlang:",
                reply_markup=get_category_list_keyboard(CategoryService.get_active_categories(db))
            )
            return
        
        # Store category info in state
        await state.update_data(category_id=category.id, category_name=category.name)
        await state.set_state(EditCategoryStates.waiting_new_name)
        
        await message.answer(
            f"✏️ <b>Kategoriyani tahrirlash</b>\n\n"
            f"Joriy nom: <b>{category.name}</b>\n\n"
            f"Yangi nomini kiriting:",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error selecting category to edit: {e}", exc_info=True)
        await message.answer(
            "❌ Xatolik yuz berdi.",
            reply_markup=get_admin_menu_keyboard()
        )
        await state.clear()
    finally:
        db.close()


@router.message(EditCategoryStates.waiting_new_name)
async def process_new_category_name(message: Message, state: FSMContext):
    """Process new category name"""
    # Check for cancel
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer(
            "❌ Bekor qilindi",
            reply_markup=get_admin_menu_keyboard()
        )
        return
    
    new_name = message.text.strip()
    
    # Validate: empty name
    if not new_name:
        await message.answer(
            "❌ Kategoriya nomi bo'sh bo'lishi mumkin emas.\n\n"
            "Yangi nomini kiriting:",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    # Validate: name too long
    if len(new_name) > 100:
        await message.answer(
            "❌ Kategoriya nomi juda uzun (maksimum 100 belgi).\n\n"
            "Qisqa kategoriya nomini kiriting:",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    data = await state.get_data()
    category_id = data.get("category_id")
    old_name = data.get("category_name")
    
    db = get_db_session()
    try:
        # Check if new name already exists (excluding current category)
        existing = CategoryService.get_category_by_name(db, new_name)
        if existing and existing.id != category_id:
            await message.answer(
                f"❌ Bu nomdagi kategoriya allaqachon mavjud.\n\n"
                f"Boshqa nom kiriting:",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        # Update category name
        updated_category = CategoryService.update_category(
            db,
            category_id=category_id,
            name=new_name
        )
        
        if updated_category:
            await message.answer(
                f"✅ Kategoriya muvaffaqiyatli tahrirlandi!\n\n"
                f"📂 Eski nom: {old_name}\n"
                f"📂 Yangi nom: {updated_category.name}",
                reply_markup=get_admin_menu_keyboard()
            )
        else:
            await message.answer(
                "❌ Kategoriya topilmadi.",
                reply_markup=get_admin_menu_keyboard()
            )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error updating category: {e}", exc_info=True)
        await message.answer(
            "❌ Xatolik yuz berdi. Qayta urinib ko'ring.",
            reply_markup=get_admin_menu_keyboard()
        )
        await state.clear()
    finally:
        db.close()


@router.message(F.text == "🗑️ Kategoriyani o'chirish")
async def start_delete_categories(message: Message, state: FSMContext):
    """Start category deletion flow"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return
    
    db = get_db_session()
    try:
        categories = CategoryService.get_active_categories(db)
        
        if not categories:
            await message.answer(
                "❌ O'chirish uchun kategoriya mavjud emas.\n\n"
                "Avval kategoriya qo'shing.",
                reply_markup=get_admin_menu_keyboard()
            )
            return
        
        await state.set_state(DeleteCategoryStates.waiting_category_selection)
        await message.answer(
            "🗑️ <b>Kategoriyani o'chirish</b>\n\n"
            "O'chirish uchun kategoriyani tanlang:",
            parse_mode="HTML",
            reply_markup=get_category_list_keyboard(categories)
        )
        
    except Exception as e:
        logger.error(f"Error starting delete categories: {e}", exc_info=True)
        await message.answer(
            "❌ Xatolik yuz berdi.",
            reply_markup=get_admin_menu_keyboard()
        )
    finally:
        db.close()


@router.message(DeleteCategoryStates.waiting_category_selection, F.text.startswith("🧸 "))
async def select_category_to_delete(message: Message, state: FSMContext):
    """Select category to delete"""
    # Check for cancel/back
    if message.text == "❌ Bekor qilish" or message.text == "⬅️ Orqaga" or message.text == "🏠 Admin menyu":
        await state.clear()
        if message.text == "🏠 Admin menyu":
            await message.answer(
                "🏠 Admin menyu",
                reply_markup=get_admin_menu_keyboard()
            )
        else:
            await message.answer(
                "❌ Bekor qilindi",
                reply_markup=get_admin_menu_keyboard()
            )
        return
    
    category_name = message.text.replace("🧸 ", "").strip()
    
    db = get_db_session()
    try:
        category = CategoryService.get_category_by_name(db, category_name)
        
        if not category:
            await message.answer(
                "❌ Kategoriya topilmadi.\n\n"
                "Kategoriyani qayta tanlang:",
                reply_markup=get_category_list_keyboard(CategoryService.get_active_categories(db))
            )
            return
        
        # Check if category has active toys
        from database.models import Toy
        active_toys_count = db.query(Toy).filter(
            Toy.category_id == category.id,
            Toy.is_active == True
        ).count()
        
        if active_toys_count > 0:
            await message.answer(
                f"❌ Bu kategoriyada {active_toys_count} ta faol o'yinchoq mavjud.\n\n"
                f"Avval o'yinchoqlarni boshqa kategoriyaga o'tkazing yoki o'chiring.\n\n"
                f"Kategoriyani o'chirish mumkin emas.",
                reply_markup=get_admin_menu_keyboard()
            )
            await state.clear()
            return
        
        # Store category info in state
        await state.update_data(category_id=category.id, category_name=category.name)
        await state.set_state(DeleteCategoryStates.waiting_confirmation)
        
        await message.answer(
            f"❗ <b>Ushbu kategoriyani o'chirmoqchimisiz?</b>\n\n"
            f"📂 Kategoriya: <b>{category.name}</b>\n\n"
            f"⚠️ Eslatma: Kategoriya o'chirilgandan keyin qayta tiklanmaydi.",
            parse_mode="HTML",
            reply_markup=get_confirm_delete_category_keyboard(category.id)
        )
        
    except Exception as e:
        logger.error(f"Error selecting category to delete: {e}", exc_info=True)
        await message.answer(
            "❌ Xatolik yuz berdi.",
            reply_markup=get_admin_menu_keyboard()
        )
        await state.clear()
    finally:
        db.close()


@router.callback_query(F.data.startswith("confirm_delete_cat_"))
async def confirm_delete_category(callback: CallbackQuery, state: FSMContext):
    """Confirm category deletion"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqi yo'q", show_alert=True)
        return
    
    try:
        category_id = int(callback.data.split("_")[-1])
        
        db = get_db_session()
        try:
            category = CategoryService.get_category_by_id(db, category_id)
            
            if not category:
                await callback.answer("❌ Kategoriya topilmadi", show_alert=True)
                await callback.message.edit_text(
                    "❌ Kategoriya topilmadi.",
                    reply_markup=None
                )
                await state.clear()
                return
            
            # Double check for active toys
            from database.models import Toy
            active_toys_count = db.query(Toy).filter(
                Toy.category_id == category.id,
                Toy.is_active == True
            ).count()
            
            if active_toys_count > 0:
                await callback.answer(
                    f"❌ Bu kategoriyada {active_toys_count} ta o'yinchoq mavjud",
                    show_alert=True
                )
                await callback.message.edit_text(
                    f"❌ Bu kategoriyada {active_toys_count} ta faol o'yinchoq mavjud.\n\n"
                    f"Avval o'yinchoqlarni boshqa kategoriyaga o'tkazing.",
                    reply_markup=None
                )
                await state.clear()
                return
            
            # Deactivate category (soft delete)
            category.is_active = False
            db.commit()
            
            await callback.message.edit_text(
                f"🗑️ Kategoriya o'chirildi: <b>{category.name}</b>",
                parse_mode="HTML",
                reply_markup=None
            )
            await callback.answer("✅ Kategoriya o'chirildi")
            await state.clear()
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error deleting category: {e}", exc_info=True)
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
        await state.clear()


@router.callback_query(F.data == "cancel_delete_cat")
async def cancel_delete_category(callback: CallbackQuery, state: FSMContext):
    """Cancel category deletion"""
    await state.clear()
    await callback.message.edit_text(
        "❌ Bekor qilindi",
        reply_markup=None
    )
    await callback.answer("❌ Bekor qilindi")


@router.message(F.text == "⬅️ Orqaga")
async def go_back_to_admin_menu(message: Message, state: FSMContext):
    """Go back to admin menu"""
    await state.clear()
    await message.answer(
        "🏠 Admin menyu",
        reply_markup=get_admin_menu_keyboard()
    )
