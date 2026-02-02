"""
User keyboard layouts - Reply keyboards for better UX
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Main menu keyboard for users - Reply keyboard"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="📦 Katalog"))
    builder.add(KeyboardButton(text="🏆 Bestseller TOP-5"))
    builder.add(KeyboardButton(text="🛒 Savatcha"))
    builder.add(KeyboardButton(text="❤️ Sevimlilar"))
    builder.add(KeyboardButton(text="📍 Do'kon manzillari"))
    builder.add(KeyboardButton(text="ℹ️ Biz haqimizda"))
    builder.add(KeyboardButton(text="📞 Bog'lanish"))
    builder.add(KeyboardButton(text="🏠 Bosh menyu"))
    builder.adjust(1)  # 1 button per row
    return builder.as_markup(resize_keyboard=True)


def get_categories_keyboard(categories: list) -> ReplyKeyboardMarkup:
    """
    Categories keyboard - Reply keyboard
    
    Args:
        categories: List of Category objects
    """
    builder = ReplyKeyboardBuilder()
    
    # Add category buttons (1 per row)
    for category in categories:
        builder.add(KeyboardButton(text=f"📂 {category.name}"))
    
    # Add back button
    builder.add(KeyboardButton(text="⬅️ Orqaga"))
    builder.add(KeyboardButton(text="🏠 Bosh menyu"))
    
    builder.adjust(1)  # 1 button per row
    return builder.as_markup(resize_keyboard=True)


def get_toy_pagination_keyboard(page: int, total_pages: int, toy_id: int, category_id: int) -> InlineKeyboardMarkup:
    """
    Toy pagination keyboard - Inline keyboard for navigation
    
    Args:
        page: Current page number (1-indexed)
        total_pages: Total number of pages
        toy_id: Current toy ID
        category_id: Category ID for pagination
    """
    builder = InlineKeyboardBuilder()
    
    # Navigation buttons (max 2 per row)
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(
            text="⬅️ Oldingi",
            callback_data=f"toy_page_{category_id}_{page - 1}"
        ))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(
            text="Keyingi ➡️",
            callback_data=f"toy_page_{category_id}_{page + 1}"
        ))
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    # Buy button
    builder.add(InlineKeyboardButton(
        text="🛒 Buyurtma berish",
        callback_data=f"order_{toy_id}"
    ))
    
    return builder.as_markup()


def get_order_confirmation_keyboard(toy_id: int) -> InlineKeyboardMarkup:
    """Order confirmation keyboard - Inline keyboard"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="✅ Ha, buyurtma berish",
        callback_data=f"confirm_order_{toy_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="❌ Bekor qilish",
        callback_data="cancel_order"
    ))
    return builder.as_markup()
