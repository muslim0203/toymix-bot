"""
Admin handlers for sales statistics
"""
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from keyboards.admin_kb import get_admin_menu_keyboard
from keyboards.stats_kb import get_stats_menu_keyboard, get_time_range_keyboard
from services.stats_service import StatsService
from database.db import get_db_session
from config import ADMIN_IDS
from states.stats_states import StatsStates

logger = logging.getLogger(__name__)
router = Router()


def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_IDS


@router.message(F.text == "📊 Sotuv statistikasi")
async def show_stats_menu(message: Message, state: FSMContext):
    """Show statistics menu"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return
    
    await state.set_state(StatsStates.select_stats_type)
    await message.answer(
        "📊 <b>Sotuv statistikasi</b>\n\n"
        "Statistika turini tanlang:",
        parse_mode="HTML",
        reply_markup=get_stats_menu_keyboard()
    )


@router.message(StatsStates.select_stats_type, F.text == "📂 Kategoriya bo'yicha")
async def select_category_stats(message: Message, state: FSMContext):
    """Select category-based statistics"""
    await state.update_data(stats_type="category")
    await state.set_state(StatsStates.select_time_range)
    await message.answer(
        "🕒 <b>Davrni tanlang:</b>",
        parse_mode="HTML",
        reply_markup=get_time_range_keyboard()
    )


@router.message(StatsStates.select_stats_type, F.text == "🧸 O'yinchoq bo'yicha")
async def select_toy_stats(message: Message, state: FSMContext):
    """Select toy-based statistics"""
    await state.update_data(stats_type="toy")
    await state.set_state(StatsStates.select_time_range)
    await message.answer(
        "🕒 <b>Davrni tanlang:</b>",
        parse_mode="HTML",
        reply_markup=get_time_range_keyboard()
    )


@router.message(StatsStates.select_time_range, F.text.in_(["📅 Haftalik", "📅 Oylik", "📅 Yillik"]))
async def show_statistics(message: Message, state: FSMContext):
    """Show statistics for selected time range"""
    # Map text to time range
    time_range_map = {
        "📅 Haftalik": "weekly",
        "📅 Oylik": "monthly",
        "📅 Yillik": "yearly"
    }
    
    time_range = time_range_map.get(message.text)
    if not time_range:
        await message.answer(
            "❌ Noto'g'ri davr tanlandi.",
            reply_markup=get_admin_menu_keyboard()
        )
        await state.clear()
        return
    
    data = await state.get_data()
    stats_type = data.get("stats_type")
    
    db = get_db_session()
    try:
        if stats_type == "category":
            stats = StatsService.get_category_stats_by_time_range(db, time_range)
            stats_text = StatsService.format_category_stats(stats, time_range)
        elif stats_type == "toy":
            stats = StatsService.get_toy_stats_by_time_range(db, time_range)
            stats_text = StatsService.format_toy_stats(stats, time_range)
        else:
            await message.answer(
                "❌ Noto'g'ri statistika turi.",
                reply_markup=get_admin_menu_keyboard()
            )
            await state.clear()
            return
        
        await message.answer(
            stats_text,
            reply_markup=get_admin_menu_keyboard()
        )
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error showing statistics: {e}", exc_info=True)
        await message.answer(
            "❌ Statistika ko'rsatishda xatolik yuz berdi.",
            reply_markup=get_admin_menu_keyboard()
        )
        await state.clear()
    finally:
        db.close()


@router.message(StatsStates.select_stats_type, F.text.in_(["⬅️ Orqaga", "🏠 Admin menyu"]))
@router.message(StatsStates.select_time_range, F.text.in_(["⬅️ Orqaga", "🏠 Admin menyu"]))
async def go_back_from_stats(message: Message, state: FSMContext):
    """Go back to admin menu"""
    await state.clear()
    if message.text == "🏠 Admin menyu":
        await message.answer(
            "🏠 Admin menyu",
            reply_markup=get_admin_menu_keyboard()
        )
    else:
        await message.answer(
            "⬅️ Orqaga",
            reply_markup=get_admin_menu_keyboard()
        )
