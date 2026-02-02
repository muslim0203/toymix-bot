"""
Keyboard layouts for bestseller management
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_bestseller_menu_keyboard() -> ReplyKeyboardMarkup:
    """Bestseller management menu keyboard - Reply keyboard"""
    builder = ReplyKeyboardBuilder()
    
    builder.add(KeyboardButton(text="➕ Bestseller qo'shish"))
    builder.add(KeyboardButton(text="🗑 Bestseller o'chirish"))
    builder.add(KeyboardButton(text="📋 Bestseller ro'yxati"))
    builder.add(KeyboardButton(text="⬅️ Orqaga"))
    builder.add(KeyboardButton(text="🏠 Admin menyu"))
    
    builder.adjust(1)  # 1 button per row
    return builder.as_markup(resize_keyboard=True)


def get_period_keyboard() -> ReplyKeyboardMarkup:
    """Period selection keyboard - Reply keyboard"""
    builder = ReplyKeyboardBuilder()
    
    builder.add(KeyboardButton(text="📅 Haftalik"))
    builder.add(KeyboardButton(text="📅 Oylik"))
    builder.add(KeyboardButton(text="📅 Yillik"))
    builder.add(KeyboardButton(text="⬅️ Orqaga"))
    builder.add(KeyboardButton(text="🏠 Admin menyu"))
    
    builder.adjust(1)  # 1 button per row
    return builder.as_markup(resize_keyboard=True)


def get_category_list_keyboard(categories: list) -> ReplyKeyboardMarkup:
    """Category list keyboard for bestseller selection - Reply keyboard"""
    builder = ReplyKeyboardBuilder()
    
    for category in categories:
        builder.add(KeyboardButton(text=f"🧸 {category.name}"))
    
    builder.add(KeyboardButton(text="⬅️ Orqaga"))
    builder.add(KeyboardButton(text="🏠 Admin menyu"))
    
    builder.adjust(1)  # 1 button per row
    return builder.as_markup(resize_keyboard=True)


def get_rank_keyboard() -> ReplyKeyboardMarkup:
    """Rank selection keyboard - Reply keyboard"""
    builder = ReplyKeyboardBuilder()
    
    builder.add(KeyboardButton(text="1️⃣ 1-o'rin"))
    builder.add(KeyboardButton(text="2️⃣ 2-o'rin"))
    builder.add(KeyboardButton(text="3️⃣ 3-o'rin"))
    builder.add(KeyboardButton(text="4️⃣ 4-o'rin"))
    builder.add(KeyboardButton(text="5️⃣ 5-o'rin"))
    builder.add(KeyboardButton(text="⬅️ Orqaga"))
    builder.add(KeyboardButton(text="🏠 Admin menyu"))
    
    builder.adjust(1)  # 1 button per row
    return builder.as_markup(resize_keyboard=True)


def get_bestseller_list_keyboard(bestsellers: list, period: str) -> ReplyKeyboardMarkup:
    """Bestseller list keyboard for deletion - Reply keyboard"""
    builder = ReplyKeyboardBuilder()
    
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    
    for bestseller in bestsellers:
        emoji = medals.get(bestseller.rank, f"{bestseller.rank}️⃣")
        source_mark = "✋" if bestseller.source == "manual" else "🤖"
        builder.add(KeyboardButton(text=f"{emoji} {source_mark} {bestseller.category_name}"))
    
    builder.add(KeyboardButton(text="⬅️ Orqaga"))
    builder.add(KeyboardButton(text="🏠 Admin menyu"))
    
    builder.adjust(1)  # 1 button per row
    return builder.as_markup(resize_keyboard=True)
