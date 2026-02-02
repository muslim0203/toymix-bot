"""
Admin handlers for bestseller category management
"""
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from keyboards.admin_kb import get_admin_menu_keyboard
from keyboards.bestseller_kb import (
    get_bestseller_menu_keyboard,
    get_period_keyboard,
    get_category_list_keyboard,
    get_rank_keyboard,
    get_bestseller_list_keyboard
)
from services.bestseller_generator import BestsellerGenerator
from services.category_service import CategoryService
from database.db import get_db_session
from config import ADMIN_IDS
from states.bestseller_states import AddBestsellerStates, DeleteBestsellerStates

logger = logging.getLogger(__name__)
router = Router()


def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_IDS


@router.message(F.text == "🏆 Bestseller boshqaruvi")
async def show_bestseller_menu(message: Message, state: FSMContext):
    """Show bestseller management menu"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return
    
    await message.answer(
        "🏆 <b>Bestseller boshqaruvi</b>\n\n"
        "Quyidagi funksiyalardan foydalaning:",
        parse_mode="HTML",
        reply_markup=get_bestseller_menu_keyboard()
    )


@router.message(F.text == "➕ Bestseller qo'shish")
async def start_add_bestseller(message: Message, state: FSMContext):
    """Start adding manual bestseller"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return
    
    await state.set_state(AddBestsellerStates.waiting_period)
    await message.answer(
        "➕ <b>Manual bestseller qo'shish</b>\n\n"
        "Davrni tanlang:",
        parse_mode="HTML",
        reply_markup=get_period_keyboard()
    )


@router.message(AddBestsellerStates.waiting_period, F.text.in_(["📅 Haftalik", "📅 Oylik", "📅 Yillik"]))
async def select_period_for_bestseller(message: Message, state: FSMContext):
    """Select period for bestseller"""
    # Check for cancel/back
    if message.text in ["⬅️ Orqaga", "🏠 Admin menyu"]:
        await state.clear()
        if message.text == "🏠 Admin menyu":
            await message.answer("🏠 Admin menyu", reply_markup=get_admin_menu_keyboard())
        else:
            await message.answer("❌ Bekor qilindi", reply_markup=get_admin_menu_keyboard())
        return
    
    period_map = {
        "📅 Haftalik": "weekly",
        "📅 Oylik": "monthly",
        "📅 Yillik": "yearly"
    }
    
    period = period_map.get(message.text)
    if not period:
        await message.answer("❌ Noto'g'ri davr tanlandi.", reply_markup=get_admin_menu_keyboard())
        await state.clear()
        return
    
    await state.update_data(period=period)
    await state.set_state(AddBestsellerStates.waiting_category)
    
    db = get_db_session()
    try:
        categories = CategoryService.get_active_categories(db)
        
        if not categories:
            await message.answer(
                "❌ Kategoriya mavjud emas.\n\n"
                "Avval kategoriya qo'shing.",
                reply_markup=get_admin_menu_keyboard()
            )
            await state.clear()
            return
        
        await message.answer(
            "🧸 Kategoriyani tanlang:",
            reply_markup=get_category_list_keyboard(categories)
        )
    finally:
        db.close()


@router.message(AddBestsellerStates.waiting_category, F.text.startswith("🧸 "))
async def select_category_for_bestseller(message: Message, state: FSMContext):
    """Select category for bestseller"""
    # Check for cancel/back
    if message.text in ["⬅️ Orqaga", "🏠 Admin menyu"]:
        await state.clear()
        if message.text == "🏠 Admin menyu":
            await message.answer("🏠 Admin menyu", reply_markup=get_admin_menu_keyboard())
        else:
            await message.answer("❌ Bekor qilindi", reply_markup=get_admin_menu_keyboard())
        return
    
    category_name = message.text.replace("🧸 ", "").strip()
    
    db = get_db_session()
    try:
        category = CategoryService.get_category_by_name(db, category_name)
        
        if not category:
            await message.answer(
                "❌ Kategoriya topilmadi.",
                reply_markup=get_admin_menu_keyboard()
            )
            await state.clear()
            return
        
        await state.update_data(category_id=category.id, category_name=category.name)
        await state.set_state(AddBestsellerStates.waiting_rank)
        
        await message.answer(
            "🏆 O'rinni tanlang (1-5):",
            reply_markup=get_rank_keyboard()
        )
    finally:
        db.close()


@router.message(AddBestsellerStates.waiting_rank)
async def process_bestseller_rank(message: Message, state: FSMContext):
    """Process bestseller rank"""
    # Check for cancel/back
    if message.text in ["⬅️ Orqaga", "🏠 Admin menyu"]:
        await state.clear()
        if message.text == "🏠 Admin menyu":
            await message.answer("🏠 Admin menyu", reply_markup=get_admin_menu_keyboard())
        else:
            await message.answer("❌ Bekor qilindi", reply_markup=get_admin_menu_keyboard())
        return
    
    # Parse rank from button text
    rank_map = {
        "1️⃣ 1-o'rin": 1,
        "2️⃣ 2-o'rin": 2,
        "3️⃣ 3-o'rin": 3,
        "4️⃣ 4-o'rin": 4,
        "5️⃣ 5-o'rin": 5
    }
    
    rank = rank_map.get(message.text)
    if not rank:
        await message.answer(
            "❌ Noto'g'ri o'rin tanlandi.\n\n"
            "1-5 o'rinlardan birini tanlang:",
            reply_markup=get_rank_keyboard()
        )
        return
    
    data = await state.get_data()
    category_id = data.get("category_id")
    period = data.get("period")
    
    db = get_db_session()
    try:
        from database.models import BestsellerCategory
        existing_manual = db.query(BestsellerCategory).filter(
            BestsellerCategory.period == period,
            BestsellerCategory.rank == rank,
            BestsellerCategory.source == "manual",
            BestsellerCategory.is_active == True
        ).first()
        
        if existing_manual and existing_manual.category_id != category_id:
            await message.answer(
                f"❌ Bu o'rin band.\n\n"
                f"O'rin {rank} da '{existing_manual.category_name}' kategoriyasi mavjud.\n\n"
                f"Boshqa o'rin tanlang:",
                reply_markup=get_rank_keyboard()
            )
            return
        
        # Create manual bestseller
        bestseller = BestsellerGenerator.create_manual_bestseller(
            db,
            category_id=category_id,
            period=period,
            rank=rank
        )
        
        if bestseller:
            await message.answer(
                f"✅ Bestseller qo'shildi!\n\n"
                f"🏆 O'rin: {rank}\n"
                f"📂 Kategoriya: {bestseller.category_name}\n"
                f"📅 Davr: {period}",
                reply_markup=get_admin_menu_keyboard()
            )
        else:
            await message.answer(
                "❌ Bestseller qo'shilmadi.",
                reply_markup=get_admin_menu_keyboard()
            )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error creating bestseller: {e}", exc_info=True)
        await message.answer(
            "❌ Xatolik yuz berdi.",
            reply_markup=get_admin_menu_keyboard()
        )
        await state.clear()
    finally:
        db.close()


@router.message(F.text == "🗑 Bestseller o'chirish")
async def start_delete_bestseller(message: Message, state: FSMContext):
    """Start deleting bestseller"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return
    
    await state.set_state(DeleteBestsellerStates.waiting_period)
    await message.answer(
        "🗑️ <b>Bestseller o'chirish</b>\n\n"
        "Davrni tanlang:",
        parse_mode="HTML",
        reply_markup=get_period_keyboard()
    )


@router.message(DeleteBestsellerStates.waiting_period, F.text.in_(["📅 Haftalik", "📅 Oylik", "📅 Yillik"]))
async def select_period_for_delete(message: Message, state: FSMContext):
    """Select period for deletion"""
    # Check for cancel/back
    if message.text in ["⬅️ Orqaga", "🏠 Admin menyu"]:
        await state.clear()
        if message.text == "🏠 Admin menyu":
            await message.answer("🏠 Admin menyu", reply_markup=get_admin_menu_keyboard())
        else:
            await message.answer("❌ Bekor qilindi", reply_markup=get_admin_menu_keyboard())
        return
    
    period_map = {
        "📅 Haftalik": "weekly",
        "📅 Oylik": "monthly",
        "📅 Yillik": "yearly"
    }
    
    period = period_map.get(message.text)
    if not period:
        await message.answer("❌ Noto'g'ri davr tanlandi.", reply_markup=get_admin_menu_keyboard())
        await state.clear()
        return
    
    await state.update_data(period=period)
    await state.set_state(DeleteBestsellerStates.waiting_bestseller)
    
    db = get_db_session()
    try:
        bestsellers = BestsellerGenerator.get_bestsellers(db, period)
        
        if not bestsellers:
            await message.answer(
                f"❌ {period} davrda bestseller mavjud emas.",
                reply_markup=get_admin_menu_keyboard()
            )
            await state.clear()
            return
        
        await message.answer(
            "🗑️ O'chirish uchun bestsellerni tanlang:",
            reply_markup=get_bestseller_list_keyboard(bestsellers, period)
        )
    finally:
        db.close()


@router.message(DeleteBestsellerStates.waiting_bestseller)
async def process_delete_bestseller(message: Message, state: FSMContext):
    """Process bestseller deletion"""
    # Check for cancel/back
    if message.text in ["⬅️ Orqaga", "🏠 Admin menyu"]:
        await state.clear()
        if message.text == "🏠 Admin menyu":
            await message.answer("🏠 Admin menyu", reply_markup=get_admin_menu_keyboard())
        else:
            await message.answer("❌ Bekor qilindi", reply_markup=get_admin_menu_keyboard())
        return
    
    # Parse category name from button text
    # Format: "🥇 ✋ Kategoriya nomi" or "🥇 🤖 Kategoriya nomi"
    category_name = message.text
    for emoji in ["🥇", "🥈", "🥉", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "✋", "🤖"]:
        category_name = category_name.replace(emoji, "").strip()
    
    data = await state.get_data()
    period = data.get("period")
    
    db = get_db_session()
    try:
        from database.models import BestsellerCategory
        bestseller = db.query(BestsellerCategory).filter(
            BestsellerCategory.period == period,
            BestsellerCategory.category_name == category_name,
            BestsellerCategory.is_active == True
        ).first()
        
        if not bestseller:
            await message.answer(
                "❌ Bestseller topilmadi.",
                reply_markup=get_admin_menu_keyboard()
            )
            await state.clear()
            return
        
        # Deactivate bestseller
        success = BestsellerGenerator.deactivate_bestseller(db, bestseller.id)
        
        if success:
            await message.answer(
                f"🗑️ Bestseller o'chirildi: {bestseller.category_name}",
                reply_markup=get_admin_menu_keyboard()
            )
        else:
            await message.answer(
                "❌ Bestseller o'chirilmadi.",
                reply_markup=get_admin_menu_keyboard()
            )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error deleting bestseller: {e}", exc_info=True)
        await message.answer(
            "❌ Xatolik yuz berdi.",
            reply_markup=get_admin_menu_keyboard()
        )
        await state.clear()
    finally:
        db.close()


@router.message(F.text == "📋 Bestseller ro'yxati")
async def list_bestsellers(message: Message):
    """List all bestsellers"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return
    
    db = get_db_session()
    try:
        periods = ["weekly", "monthly", "yearly"]
        period_names = {
            "weekly": "Haftalik",
            "monthly": "Oylik",
            "yearly": "Yillik"
        }
        
        text = "📋 <b>Bestseller ro'yxati</b>\n\n"
        
        for period in periods:
            bestsellers = BestsellerGenerator.get_bestsellers(db, period)
            if bestsellers:
                text += f"📅 <b>{period_names[period]}</b>:\n"
                medals = {1: "🥇", 2: "🥈", 3: "🥉"}
                for bestseller in bestsellers:
                    emoji = medals.get(bestseller.rank, f"{bestseller.rank}️⃣")
                    source_mark = "✋ Manual" if bestseller.source == "manual" else "🤖 Auto"
                    text += f"{emoji} {bestseller.category_name} ({source_mark})\n"
                text += "\n"
        
        if text == "📋 <b>Bestseller ro'yxati</b>\n\n":
            text += "❌ Bestseller mavjud emas."
        
        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=get_admin_menu_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error listing bestsellers: {e}", exc_info=True)
        await message.answer(
            "❌ Xatolik yuz berdi.",
            reply_markup=get_admin_menu_keyboard()
        )
    finally:
        db.close()


@router.message(F.text == "⬅️ Orqaga")
async def go_back_from_bestseller(message: Message, state: FSMContext):
    """Go back to admin menu"""
    await state.clear()
    await message.answer(
        "🏠 Admin menyu",
        reply_markup=get_admin_menu_keyboard()
    )
