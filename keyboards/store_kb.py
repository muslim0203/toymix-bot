"""
Keyboard layouts for store locations
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_store_list_keyboard(stores: list) -> ReplyKeyboardMarkup:
    """Store list keyboard - Reply keyboard"""
    builder = ReplyKeyboardBuilder()
    
    for store in stores:
        builder.add(KeyboardButton(text=f"🏬 {store.name}"))
    
    builder.add(KeyboardButton(text="⬅️ Orqaga"))
    builder.add(KeyboardButton(text="🏠 Bosh menyu"))
    
    builder.adjust(1)  # 1 button per row
    return builder.as_markup(resize_keyboard=True)


def get_admin_store_menu_keyboard() -> ReplyKeyboardMarkup:
    """Admin store management menu keyboard - Reply keyboard"""
    builder = ReplyKeyboardBuilder()
    
    builder.add(KeyboardButton(text="➕ Manzil qo'shish"))
    builder.add(KeyboardButton(text="🗑 Manzil o'chirish"))
    builder.add(KeyboardButton(text="📋 Manzillar ro'yxati"))
    builder.add(KeyboardButton(text="⬅️ Orqaga"))
    builder.add(KeyboardButton(text="🏠 Admin menyu"))
    
    builder.adjust(1)  # 1 button per row
    return builder.as_markup(resize_keyboard=True)
