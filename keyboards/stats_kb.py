"""
Keyboard layouts for statistics
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_stats_menu_keyboard() -> ReplyKeyboardMarkup:
    """Statistics menu keyboard - Reply keyboard"""
    builder = ReplyKeyboardBuilder()
    
    builder.add(KeyboardButton(text="📂 Kategoriya bo'yicha"))
    builder.add(KeyboardButton(text="🧸 O'yinchoq bo'yicha"))
    builder.add(KeyboardButton(text="⬅️ Orqaga"))
    builder.add(KeyboardButton(text="🏠 Admin menyu"))
    
    builder.adjust(1)  # 1 button per row
    return builder.as_markup(resize_keyboard=True)


def get_time_range_keyboard() -> ReplyKeyboardMarkup:
    """Time range selection keyboard - Reply keyboard"""
    builder = ReplyKeyboardBuilder()
    
    builder.add(KeyboardButton(text="📅 Haftalik"))
    builder.add(KeyboardButton(text="📅 Oylik"))
    builder.add(KeyboardButton(text="📅 Yillik"))
    builder.add(KeyboardButton(text="⬅️ Orqaga"))
    builder.add(KeyboardButton(text="🏠 Admin menyu"))
    
    builder.adjust(1)  # 1 button per row
    return builder.as_markup(resize_keyboard=True)
