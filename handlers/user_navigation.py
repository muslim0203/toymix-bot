"""
Navigation handlers for back buttons
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

from keyboards.user_kb import get_categories_keyboard, get_main_menu_keyboard
from services.category_service import CategoryService
from database.db import get_db_session

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data.startswith("back_to_category_"))
async def back_to_category(callback: CallbackQuery):
    """Go back to category list"""
    try:
        category_id = int(callback.data.split("_")[-1])
        
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
        logger.error(f"Error going back to category: {e}", exc_info=True)
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
