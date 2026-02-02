"""
Admin handlers for managing order contacts
"""
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards.admin_kb import get_admin_menu_keyboard
from keyboards.category_manage_kb import get_cancel_keyboard
from services.order_contact_service import OrderContactService
from database.db import get_db_session
from config import ADMIN_IDS

logger = logging.getLogger(__name__)
router = Router()


class AddContactStates(StatesGroup):
    """FSM states for adding a contact"""
    waiting_contact_value = State()


class DeleteContactStates(StatesGroup):
    """FSM states for deleting a contact"""
    waiting_contact_selection = State()


def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_IDS


@router.message(F.text == "📞 Buyurtma kontaktlari")
async def show_contacts_menu(message: Message):
    """Show contacts management menu"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return
    
    menu_text = (
        "📞 <b>Buyurtma kontaktlari boshqaruvi</b>\n\n"
        "Quyidagi funksiyalardan foydalaning:"
    )
    
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    from aiogram.utils.keyboard import ReplyKeyboardBuilder
    
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="➕ Kontakt qo'shish"))
    builder.add(KeyboardButton(text="🗑 Kontakt o'chirish"))
    builder.add(KeyboardButton(text="📋 Kontaktlar ro'yxati"))
    builder.add(KeyboardButton(text="⬅️ Orqaga"))
    builder.add(KeyboardButton(text="🏠 Admin menyu"))
    builder.adjust(1)
    
    await message.answer(
        menu_text,
        parse_mode="HTML",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )


@router.message(F.text == "➕ Kontakt qo'shish")
async def start_add_contact(message: Message, state: FSMContext):
    """Start adding a new contact"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return
    
    await state.set_state(AddContactStates.waiting_contact_value)
    await message.answer(
        "➕ <b>Yangi kontakt qo'shish</b>\n\n"
        "Telefon raqam yoki @username kiriting:\n\n"
        "Masalan:\n"
        "☎️ +998901234567\n"
        "💬 @toymix_admin",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )


@router.message(AddContactStates.waiting_contact_value)
async def process_contact_value(message: Message, state: FSMContext):
    """Process contact value"""
    # Check for cancel
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer(
            "❌ Bekor qilindi",
            reply_markup=get_admin_menu_keyboard()
        )
        return
    
    contact_value = message.text.strip()
    
    # Validate: empty input
    if not contact_value:
        await message.answer(
            "❌ Kontakt bo'sh bo'lishi mumkin emas.\n\n"
            "Telefon raqam yoki @username kiriting:",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    # Validate: too long
    if len(contact_value) > 255:
        await message.answer(
            "❌ Kontakt juda uzun (maksimum 255 belgi).\n\n"
            "Qisqa kontakt kiriting:",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    db = get_db_session()
    try:
        # Check for duplicates
        existing = OrderContactService.get_contact_by_value(db, contact_value)
        if existing:
            await message.answer(
                f"❌ Bu kontakt allaqachon mavjud.\n\n"
                f"Boshqa kontakt kiriting:",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        # Create contact
        contact = OrderContactService.create_contact(db, contact_value)
        
        contact_type = "💬 Username" if contact_value.startswith("@") else "☎️ Telefon"
        await message.answer(
            f"✅ Kontakt muvaffaqiyatli qo'shildi!\n\n"
            f"{contact_type}: {contact.contact_value}",
            reply_markup=get_admin_menu_keyboard()
        )
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error creating contact: {e}", exc_info=True)
        await message.answer(
            "❌ Xatolik yuz berdi. Qayta urinib ko'ring.",
            reply_markup=get_admin_menu_keyboard()
        )
        await state.clear()
    finally:
        db.close()


@router.message(F.text == "🗑 Kontakt o'chirish")
async def start_delete_contact(message: Message, state: FSMContext):
    """Start deleting a contact"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return
    
    db = get_db_session()
    try:
        contacts = OrderContactService.get_active_contacts(db)
        
        if not contacts:
            await message.answer(
                "❌ O'chirish uchun kontakt mavjud emas.\n\n"
                "Avval kontakt qo'shing.",
                reply_markup=get_admin_menu_keyboard()
            )
            return
        
        await state.set_state(DeleteContactStates.waiting_contact_selection)
        
        from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
        from aiogram.utils.keyboard import ReplyKeyboardBuilder
        
        builder = ReplyKeyboardBuilder()
        for contact in contacts:
            contact_display = f"📞 {contact.contact_value}"
            builder.add(KeyboardButton(text=contact_display))
        builder.add(KeyboardButton(text="⬅️ Orqaga"))
        builder.add(KeyboardButton(text="🏠 Admin menyu"))
        builder.adjust(1)
        
        await message.answer(
            "🗑️ <b>Kontaktni o'chirish</b>\n\n"
            "O'chirish uchun kontaktni tanlang:",
            parse_mode="HTML",
            reply_markup=builder.as_markup(resize_keyboard=True)
        )
        
    except Exception as e:
        logger.error(f"Error starting delete contact: {e}", exc_info=True)
        await message.answer(
            "❌ Xatolik yuz berdi.",
            reply_markup=get_admin_menu_keyboard()
        )
    finally:
        db.close()


@router.message(DeleteContactStates.waiting_contact_selection, F.text.startswith("📞 "))
async def process_delete_contact(message: Message, state: FSMContext):
    """Process contact deletion"""
    # Check for cancel/back
    if message.text == "⬅️ Orqaga" or message.text == "🏠 Admin menyu":
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
    
    contact_value = message.text.replace("📞 ", "").strip()
    
    db = get_db_session()
    try:
        contact = OrderContactService.get_contact_by_value(db, contact_value)
        
        if not contact:
            await message.answer(
                "❌ Kontakt topilmadi.",
                reply_markup=get_admin_menu_keyboard()
            )
            await state.clear()
            return
        
        # Deactivate contact (soft delete)
        deactivated = OrderContactService.deactivate_contact(db, contact.id)
        
        if deactivated:
            await message.answer(
                f"🗑️ Kontakt o'chirildi: {contact.contact_value}",
                reply_markup=get_admin_menu_keyboard()
            )
        else:
            await message.answer(
                "❌ Kontakt o'chirilmadi.",
                reply_markup=get_admin_menu_keyboard()
            )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error deleting contact: {e}", exc_info=True)
        await message.answer(
            "❌ Xatolik yuz berdi.",
            reply_markup=get_admin_menu_keyboard()
        )
        await state.clear()
    finally:
        db.close()


@router.message(F.text == "📋 Kontaktlar ro'yxati")
async def list_contacts(message: Message):
    """List all active contacts"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return
    
    db = get_db_session()
    try:
        contacts = OrderContactService.get_active_contacts(db)
        contacts_text = OrderContactService.format_contacts_for_display(contacts)
        
        await message.answer(
            contacts_text,
            reply_markup=get_admin_menu_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error listing contacts: {e}", exc_info=True)
        await message.answer(
            "❌ Xatolik yuz berdi.",
            reply_markup=get_admin_menu_keyboard()
        )
    finally:
        db.close()


@router.message(F.text == "⬅️ Orqaga")
async def go_back_from_contacts(message: Message, state: FSMContext):
    """Go back to admin menu"""
    await state.clear()
    await message.answer(
        "🏠 Admin menyu",
        reply_markup=get_admin_menu_keyboard()
    )
