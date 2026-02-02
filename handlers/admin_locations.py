"""
Admin handlers for store location management
"""
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, Location
from aiogram.fsm.context import FSMContext

from keyboards.admin_kb import get_admin_menu_keyboard
from keyboards.store_kb import get_admin_store_menu_keyboard, get_store_list_keyboard
from keyboards.category_manage_kb import get_cancel_keyboard
from services.store_location_service import StoreLocationService
from database.db import get_db_session
from config import ADMIN_IDS
from states.store_states import AddStoreLocationStates, DeleteStoreLocationStates

logger = logging.getLogger(__name__)
router = Router()


def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_IDS


@router.message(F.text == "🏬 Do'kon manzillari")
async def show_store_menu(message: Message):
    """Show store location management menu"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return
    
    await message.answer(
        "🏬 <b>Do'kon manzillari boshqaruvi</b>\n\n"
        "Quyidagi funksiyalardan foydalaning:",
        parse_mode="HTML",
        reply_markup=get_admin_store_menu_keyboard()
    )


@router.message(F.text == "➕ Manzil qo'shish")
async def start_add_store_location(message: Message, state: FSMContext):
    """Start adding a new store location"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return
    
    await state.set_state(AddStoreLocationStates.waiting_name)
    await message.answer(
        "➕ <b>Yangi do'kon manzili qo'shish</b>\n\n"
        "Do'kon nomini kiriting:\n\n"
        "Masalan: Yaypan Toymix - Chilonzor filiali",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )


@router.message(AddStoreLocationStates.waiting_name)
async def process_store_name(message: Message, state: FSMContext):
    """Process store name"""
    # Check for cancel
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer(
            "❌ Bekor qilindi",
            reply_markup=get_admin_menu_keyboard()
        )
        return
    
    store_name = message.text.strip()
    
    if not store_name:
        await message.answer(
            "❌ Do'kon nomi bo'sh bo'lishi mumkin emas.\n\n"
            "Do'kon nomini kiriting:",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    await state.update_data(name=store_name)
    await state.set_state(AddStoreLocationStates.waiting_address)
    await message.answer(
        "📍 To'liq manzilni kiriting:\n\n"
        "Masalan: Toshkent shahar, Chilonzor tumani, Bunyodkor ko'chasi, 15-uy",
        reply_markup=get_cancel_keyboard()
    )


@router.message(AddStoreLocationStates.waiting_address)
async def process_store_address(message: Message, state: FSMContext):
    """Process store address"""
    # Check for cancel
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer(
            "❌ Bekor qilindi",
            reply_markup=get_admin_menu_keyboard()
        )
        return
    
    address = message.text.strip()
    
    if not address:
        await message.answer(
            "❌ Manzil bo'sh bo'lishi mumkin emas.\n\n"
            "To'liq manzilni kiriting:",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    await state.update_data(address_text=address)
    await state.set_state(AddStoreLocationStates.waiting_location)
    await message.answer(
        "📍 <b>Lokatsiya yuboring</b>\n\n"
        "Telegram orqali lokatsiya yuboring:\n\n"
        "1️⃣ Telegram'da 📎 tugmasini bosing\n"
        "2️⃣ \"Lokatsiya\" ni tanlang\n"
        "3️⃣ Xaritadan do'kon joylashgan joyni tanlang\n"
        "4️⃣ \"Lokatsiyani yuborish\" tugmasini bosing\n\n"
        "Yoki koordinatalarni qo'lda kiriting (masalan: 41.2995, 69.2401)",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )


@router.message(AddStoreLocationStates.waiting_location, F.location)
async def process_location(message: Message, state: FSMContext):
    """Process Telegram location and save store location"""
    location = message.location
    
    if not location:
        await message.answer(
            "❌ Lokatsiya topilmadi.\n\n"
            "Iltimos, Telegram orqali lokatsiya yuboring yoki koordinatalarni kiriting.",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    # Get latitude and longitude from Telegram location
    latitude = str(location.latitude)
    longitude = str(location.longitude)
    
    data = await state.get_data()
    name = data.get("name")
    address_text = data.get("address_text")
    
    if not name or not address_text:
        await message.answer(
            "❌ Xatolik: ma'lumotlar to'liq emas.",
            reply_markup=get_admin_menu_keyboard()
        )
        await state.clear()
        return
    
    db = get_db_session()
    try:
        store_location = StoreLocationService.create_location(
            db,
            name=name,
            address_text=address_text,
            latitude=latitude,
            longitude=longitude
        )
        
        await message.answer(
            f"✅ Do'kon manzili qo'shildi!\n\n"
            f"🏬 {store_location.name}\n"
            f"📍 {store_location.address_text}\n"
            f"🌍 Koordinatalar: {latitude}, {longitude}",
            reply_markup=get_admin_menu_keyboard()
        )
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error creating store location: {e}", exc_info=True)
        await message.answer(
            "❌ Xatolik yuz berdi. Qayta urinib ko'ring.",
            reply_markup=get_admin_menu_keyboard()
        )
        await state.clear()
    finally:
        db.close()


@router.message(AddStoreLocationStates.waiting_location)
async def process_location_text(message: Message, state: FSMContext):
    """Process location as text (coordinates) - fallback option"""
    # Check for cancel
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer(
            "❌ Bekor qilindi",
            reply_markup=get_admin_menu_keyboard()
        )
        return
    
    # Try to parse coordinates from text
    # Format: "latitude, longitude" or "latitude longitude"
    text = message.text.strip()
    
    # Try comma-separated format
    if "," in text:
        parts = [p.strip() for p in text.split(",")]
        if len(parts) == 2:
            try:
                latitude = float(parts[0])
                longitude = float(parts[1])
                
                # Validate coordinates
                if not (-90 <= latitude <= 90):
                    raise ValueError("Latitude out of range")
                if not (-180 <= longitude <= 180):
                    raise ValueError("Longitude out of range")
                
                data = await state.get_data()
                name = data.get("name")
                address_text = data.get("address_text")
                
                if not name or not address_text:
                    await message.answer(
                        "❌ Xatolik: ma'lumotlar to'liq emas.",
                        reply_markup=get_admin_menu_keyboard()
                    )
                    await state.clear()
                    return
                
                db = get_db_session()
                try:
                    store_location = StoreLocationService.create_location(
                        db,
                        name=name,
                        address_text=address_text,
                        latitude=str(latitude),
                        longitude=str(longitude)
                    )
                    
                    await message.answer(
                        f"✅ Do'kon manzili qo'shildi!\n\n"
                        f"🏬 {store_location.name}\n"
                        f"📍 {store_location.address_text}\n"
                        f"🌍 Koordinatalar: {latitude}, {longitude}",
                        reply_markup=get_admin_menu_keyboard()
                    )
                    await state.clear()
                    
                except Exception as e:
                    logger.error(f"Error creating store location: {e}", exc_info=True)
                    await message.answer(
                        "❌ Xatolik yuz berdi. Qayta urinib ko'ring.",
                        reply_markup=get_admin_menu_keyboard()
                    )
                    await state.clear()
                finally:
                    db.close()
                return
            except ValueError as e:
                await message.answer(
                    "❌ Noto'g'ri koordinatalar.\n\n"
                    "Format: <code>latitude, longitude</code>\n"
                    "Masalan: <code>41.2995, 69.2401</code>\n\n"
                    "Yoki Telegram orqali lokatsiya yuboring.",
                    parse_mode="HTML",
                    reply_markup=get_cancel_keyboard()
                )
                return
    
    # If not parsed, show error
    await message.answer(
        "❌ Lokatsiya formatini noto'g'ri.\n\n"
        "Iltimos, quyidagi usullardan birini tanlang:\n\n"
        "1️⃣ Telegram orqali 📍 lokatsiya yuboring\n"
        "2️⃣ Koordinatalarni kiriting: <code>latitude, longitude</code>\n"
        "Masalan: <code>41.2995, 69.2401</code>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )


@router.message(F.text == "🗑 Manzil o'chirish")
async def start_delete_store_location(message: Message, state: FSMContext):
    """Start deleting a store location"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return
    
    db = get_db_session()
    try:
        stores = StoreLocationService.get_active_locations(db)
        
        if not stores:
            await message.answer(
                "❌ O'chirish uchun do'kon mavjud emas.",
                reply_markup=get_admin_menu_keyboard()
            )
            return
        
        await state.set_state(DeleteStoreLocationStates.waiting_location_selection)
        await message.answer(
            "🗑️ <b>Do'kon manzilini o'chirish</b>\n\n"
            "O'chirish uchun do'konni tanlang:",
            parse_mode="HTML",
            reply_markup=get_store_list_keyboard(stores)
        )
        
    except Exception as e:
        logger.error(f"Error starting delete store: {e}", exc_info=True)
        await message.answer(
            "❌ Xatolik yuz berdi.",
            reply_markup=get_admin_menu_keyboard()
        )
    finally:
        db.close()


@router.message(DeleteStoreLocationStates.waiting_location_selection, F.text.startswith("🏬 "))
async def process_delete_store_location(message: Message, state: FSMContext):
    """Process store location deletion"""
    # Check for cancel/back
    if message.text in ["⬅️ Orqaga", "🏠 Admin menyu", "🏠 Bosh menyu"]:
        await state.clear()
        if "Admin" in message.text:
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
    
    store_name = message.text.replace("🏬 ", "").strip()
    
    db = get_db_session()
    try:
        store = StoreLocationService.get_location_by_name(db, store_name)
        
        if not store:
            await message.answer(
                "❌ Do'kon topilmadi.",
                reply_markup=get_admin_menu_keyboard()
            )
            await state.clear()
            return
        
        # Deactivate store (soft delete)
        deactivated = StoreLocationService.deactivate_location(db, store.id)
        
        if deactivated:
            await message.answer(
                f"🗑️ Do'kon manzili o'chirildi: {store.name}",
                reply_markup=get_admin_menu_keyboard()
            )
        else:
            await message.answer(
                "❌ Do'kon o'chirilmadi.",
                reply_markup=get_admin_menu_keyboard()
            )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error deleting store location: {e}", exc_info=True)
        await message.answer(
            "❌ Xatolik yuz berdi.",
            reply_markup=get_admin_menu_keyboard()
        )
        await state.clear()
    finally:
        db.close()


@router.message(F.text == "📋 Manzillar ro'yxati")
async def list_store_locations(message: Message):
    """List all store locations"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return
    
    db = get_db_session()
    try:
        stores = StoreLocationService.get_active_locations(db)
        
        if not stores:
            await message.answer(
                "❌ Do'kon manzillari mavjud emas.",
                reply_markup=get_admin_menu_keyboard()
            )
            return
        
        text = "📋 <b>Do'kon manzillari ro'yxati</b>\n\n"
        
        for idx, store in enumerate(stores, 1):
            text += f"{idx}. 🏬 <b>{store.name}</b>\n"
            text += f"   📍 {store.address_text}\n\n"
        
        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=get_admin_menu_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error listing store locations: {e}", exc_info=True)
        await message.answer(
            "❌ Xatolik yuz berdi.",
            reply_markup=get_admin_menu_keyboard()
        )
    finally:
        db.close()


@router.message(F.text == "⬅️ Orqaga")
async def go_back_from_stores(message: Message, state: FSMContext):
    """Go back to admin menu"""
    await state.clear()
    await message.answer(
        "🏠 Admin menyu",
        reply_markup=get_admin_menu_keyboard()
    )
