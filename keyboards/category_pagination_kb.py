"""
Category pagination keyboard for catalog browsing
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_category_pagination_keyboard(category_id: int, page: int, total_count: int, page_size: int = 10) -> InlineKeyboardMarkup:
    """
    Get pagination keyboard for category products
    
    Args:
        category_id: Category ID
        page: Current page (0-indexed)
        total_count: Total number of products in category
        page_size: Items per page (default: 10)
        
    Returns:
        InlineKeyboardMarkup with Previous/Next buttons
    """
    builder = InlineKeyboardBuilder()
    
    # Calculate total pages
    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
    
    # Navigation buttons
    nav_buttons = []
    
    # Show Previous button only if page > 0
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="⬅️ Oldingi",
            callback_data=f"catpage:{category_id}:{page - 1}"
        ))
    
    # Show Next button only if more pages exist
    if (page + 1) * page_size < total_count:
        nav_buttons.append(InlineKeyboardButton(
            text="➡️ Keyingi",
            callback_data=f"catpage:{category_id}:{page + 1}"
        ))
    
    # Add navigation buttons in one row
    if nav_buttons:
        builder.row(*nav_buttons)
    
    # Back to categories button
    builder.add(InlineKeyboardButton(
        text="⬅️ Kategoriyalarga qaytish",
        callback_data="back_to_categories"
    ))
    
    return builder.as_markup()
