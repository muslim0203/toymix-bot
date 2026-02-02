"""
Keyboard layouts for category management
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def get_category_list_keyboard(categories: list, action_prefix: str = "cat_") -> ReplyKeyboardMarkup:
    """
    Category list keyboard for management - Reply keyboard
    
    Args:
        categories: List of Category objects
        action_prefix: Prefix for callback data (e.g., "edit_cat_", "delete_cat_")
    """
    builder = ReplyKeyboardBuilder()
    
    # Add category buttons (1 per row)
    for category in categories:
        builder.add(KeyboardButton(text=f"🧸 {category.name}"))
    
    # Add back button
    builder.add(KeyboardButton(text="⬅️ Orqaga"))
    builder.add(KeyboardButton(text="🏠 Admin menyu"))
    
    builder.adjust(1)  # 1 button per row
    return builder.as_markup(resize_keyboard=True)


def get_confirm_delete_category_keyboard(category_id: int) -> InlineKeyboardMarkup:
    """Confirmation keyboard for deleting a category - Inline keyboard"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="🗑 Ha, o'chirish",
        callback_data=f"confirm_delete_cat_{category_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="❌ Bekor qilish",
        callback_data="cancel_delete_cat"
    ))
    return builder.as_markup()


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Cancel operation keyboard - Reply keyboard"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="❌ Bekor qilish"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)
