"""
User handlers for store locations
"""
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message

from keyboards.user_kb import get_main_menu_keyboard
from keyboards.store_kb import get_store_list_keyboard
from services.store_location_service import StoreLocationService
from database.db import get_db_session

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text == "📍 Do'kon manzillari")
async def show_store_locations(message: Message):
    """Show store locations menu"""
    db = get_db_session()
    try:
        stores = StoreLocationService.get_active_locations(db)
        
        if not stores:
            await message.answer(
                "❌ Hozircha do'kon manzillari mavjud emas.\n\n"
                "Tez orada qo'shiladi!",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        await message.answer(
            "🏬 <b>Do'konlar ro'yxati</b>\n\n"
            "Manzilni ko'rish uchun do'konni tanlang:",
            parse_mode="HTML",
            reply_markup=get_store_list_keyboard(stores)
        )
        
    except Exception as e:
        logger.error(f"Error showing store locations: {e}", exc_info=True)
        await message.answer(
            "❌ Xatolik yuz berdi.",
            reply_markup=get_main_menu_keyboard()
        )
    finally:
        db.close()


@router.message(F.text.startswith("🏬 "))
async def show_store_location(message: Message, bot: Bot):
    """Show specific store location with map"""
    store_name = message.text.replace("🏬 ", "").strip()
    
    # Check for back/main menu
    if store_name in ["⬅️ Orqaga", "🏠 Bosh menyu"]:
        if store_name == "🏠 Bosh menyu":
            await message.answer(
                "🏠 Bosh menyu",
                reply_markup=get_main_menu_keyboard()
            )
        return
    
    db = get_db_session()
    try:
        store = StoreLocationService.get_location_by_name(db, store_name)
        
        if not store:
            await message.answer(
                "❌ Do'kon topilmadi.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        # Send location pin first (better UX)
        try:
            latitude = float(store.latitude)
            longitude = float(store.longitude)
            
            # Send location pin
            await bot.send_location(
                chat_id=message.chat.id,
                latitude=latitude,
                longitude=longitude
            )
            
            # Then send address text
            address_text = (
                f"🏬 <b>{store.name}</b>\n\n"
                f"📍 <b>Manzil:</b>\n"
                f"{store.address_text}"
            )
            
            await message.answer(
                address_text,
                parse_mode="HTML",
                reply_markup=get_main_menu_keyboard()
            )
            
        except (ValueError, TypeError) as e:
            logger.error(f"Error sending location: {e}")
            # Fallback: send text only if coordinates are invalid
            address_text = (
                f"🏬 <b>{store.name}</b>\n\n"
                f"📍 <b>Manzil:</b>\n"
                f"{store.address_text}\n\n"
                f"⚠️ Xarita koordinatalari mavjud emas."
            )
            
            await message.answer(
                address_text,
                parse_mode="HTML",
                reply_markup=get_main_menu_keyboard()
            )
        
    except Exception as e:
        logger.error(f"Error showing store location: {e}", exc_info=True)
        await message.answer(
            "❌ Xatolik yuz berdi.",
            reply_markup=get_main_menu_keyboard()
        )
    finally:
        db.close()


@router.message(F.text.in_(["⬅️ Orqaga", "🏠 Bosh menyu"]))
async def go_back_from_stores(message: Message):
    """Go back to main menu"""
    await message.answer(
        "🏠 Bosh menyu",
        reply_markup=get_main_menu_keyboard()
    )
