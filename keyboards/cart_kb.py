"""
Keyboard layouts for shopping cart
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_cart_actions_keyboard() -> InlineKeyboardMarkup:
    """Get inline keyboard for cart actions"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="🗑 Savatchani tozalash",
        callback_data="clear_cart"
    ))
    builder.add(InlineKeyboardButton(
        text="🛒 Buyurtma berish",
        callback_data="order_from_cart"
    ))
    
    builder.adjust(1)  # 1 button per row
    return builder.as_markup()
