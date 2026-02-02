"""
User handlers for viewing bestseller categories
"""
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards.user_kb import get_main_menu_keyboard
from keyboards.bestseller_kb import get_period_keyboard
from services.bestseller_generator import BestsellerGenerator
from database.db import get_db_session

logger = logging.getLogger(__name__)
router = Router()


class BestsellerViewStates(StatesGroup):
    """FSM states for viewing bestsellers"""
    waiting_period = State()


@router.message(F.text == "🏆 Bestseller TOP-5")
async def show_bestseller_periods(message: Message, state: FSMContext):
    """Show bestseller period selection"""
    await state.set_state(BestsellerViewStates.waiting_period)
    await message.answer(
        "🏆 <b>Bestseller TOP-5</b>\n\n"
        "Davrni tanlang:",
        parse_mode="HTML",
        reply_markup=get_period_keyboard()
    )


@router.message(BestsellerViewStates.waiting_period, F.text.in_(["📅 Haftalik", "📅 Oylik", "📅 Yillik"]))
async def show_bestsellers(message: Message, state: FSMContext):
    """Show bestsellers for selected period"""
    # Check for cancel/back
    if message.text in ["⬅️ Orqaga", "🏠 Admin menyu", "🏠 Bosh menyu"]:
        await state.clear()
        await message.answer(
            "🏠 Bosh menyu",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    period_map = {
        "📅 Haftalik": "weekly",
        "📅 Oylik": "monthly",
        "📅 Yillik": "yearly"
    }
    
    period = period_map.get(message.text)
    if not period:
        await message.answer(
            "❌ Noto'g'ri davr tanlandi.",
            reply_markup=get_main_menu_keyboard()
        )
        await state.clear()
        return
    
    db = get_db_session()
    try:
        bestsellers = BestsellerGenerator.get_bestsellers(db, period)
        bestsellers_text = BestsellerGenerator.format_bestsellers_for_display(bestsellers, period)
        
        await message.answer(
            bestsellers_text,
            reply_markup=get_main_menu_keyboard()
        )
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error showing bestsellers: {e}", exc_info=True)
        await message.answer(
            "❌ Xatolik yuz berdi.",
            reply_markup=get_main_menu_keyboard()
        )
        await state.clear()
    finally:
        db.close()


@router.message(BestsellerViewStates.waiting_period, F.text.in_(["⬅️ Orqaga", "🏠 Bosh menyu"]))
async def go_back_from_bestseller_view(message: Message, state: FSMContext):
    """Go back to main menu"""
    await state.clear()
    await message.answer(
        "🏠 Bosh menyu",
        reply_markup=get_main_menu_keyboard()
    )
