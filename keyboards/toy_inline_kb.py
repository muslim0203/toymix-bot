"""
Inline keyboards for toy viewing (cart and favorites)
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_toy_actions_keyboard(toy_id: int, is_favorite: bool = False) -> InlineKeyboardMarkup:
    """
    Get inline keyboard for toy actions (add to cart, add to favorites)
    
    Args:
        toy_id: Toy ID
        is_favorite: Whether toy is already in favorites
        
    Returns:
        InlineKeyboardMarkup
    """
    builder = InlineKeyboardBuilder()
    
    # Add to cart button
    builder.add(InlineKeyboardButton(
        text="➕ Savatchaga qo'shish",
        callback_data=f"add_to_cart_{toy_id}"
    ))
    
    # Add to favorites button
    if is_favorite:
        favorite_text = "❤️ Sevimlilarda"
        favorite_callback = f"remove_from_favorites_{toy_id}"
    else:
        favorite_text = "❤️ Sevimlilarga qo'shish"
        favorite_callback = f"add_to_favorites_{toy_id}"
    
    builder.add(InlineKeyboardButton(
        text=favorite_text,
        callback_data=favorite_callback
    ))
    
    builder.adjust(1)  # 1 button per row
    return builder.as_markup()


def get_cart_item_keyboard(cart_item_id: int) -> InlineKeyboardMarkup:
    """
    Get inline keyboard for cart item actions
    
    Args:
        cart_item_id: Cart item ID
        
    Returns:
        InlineKeyboardMarkup
    """
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="➖ O'chirish",
        callback_data=f"remove_from_cart_{cart_item_id}"
    ))
    
    builder.adjust(1)
    return builder.as_markup()


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


def get_favorite_toy_keyboard(toy_id: int) -> InlineKeyboardMarkup:
    """
    Get inline keyboard for favorite toy actions
    
    Args:
        toy_id: Toy ID
        
    Returns:
        InlineKeyboardMarkup
    """
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="➕ Savatchaga qo'shish",
        callback_data=f"add_to_cart_{toy_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="🗑 Sevimlilardan o'chirish",
        callback_data=f"remove_from_favorites_{toy_id}"
    ))
    
    builder.adjust(1)  # 1 button per row
    return builder.as_markup()
