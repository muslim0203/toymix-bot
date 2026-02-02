"""
User handlers for About Us section
"""
import logging
from aiogram import Router, F
from aiogram.types import Message

from keyboards.user_kb import get_main_menu_keyboard

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text == "ℹ️ Biz haqimizda")
async def show_about_us(message: Message):
    """Show About Us information"""
    about_text = (
        "🧸 <b>Yaypan Toymix — bolalar quvonchi manbai!</b>\n\n"
        "Biz bolalar uchun sifatli, xavfsiz va rivojlantiruvchi o'yinchoqlarni taqdim etishga ixtisoslashganmiz. "
        "Assortimentimizda yumshoq o'yinchoqlar, konstruktorlar, mashinalar, aqlni charxlovchi va sovg'alik mahsulotlar mavjud.\n\n"
        "🎯 <b>Maqsadimiz</b> — har bir bolaga quvonch ulashish, ota-onalarga esa ishonchli tanlov taklif qilish.\n\n"
        "📦 Qulay narxlar\n"
        "🚚 Tezkor xizmat\n"
        "🤝 Ishonchli hamkorlik\n\n"
        "<b>Yaypan Toymix — quvonch ulashamiz!</b>"
    )
    
    await message.answer(
        about_text,
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )


@router.message(F.text == "📞 Bog'lanish")
async def show_contact_info(message: Message):
    """Show contact information"""
    from services.order_contact_service import OrderContactService
    from database.db import get_db_session
    
    db = get_db_session()
    try:
        contacts = OrderContactService.get_active_contacts(db)
        contact_text = OrderContactService.format_contacts_for_display(contacts)
        
        await message.answer(
            f"📞 <b>Bog'lanish</b>\n\n{contact_text}",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error showing contact info: {e}", exc_info=True)
        await message.answer(
            "❌ Xatolik yuz berdi.",
            reply_markup=get_main_menu_keyboard()
        )
    finally:
        db.close()
