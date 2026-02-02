"""
Admin keyboard layouts - Reply keyboards for better UX
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def get_admin_menu_keyboard() -> ReplyKeyboardMarkup:
    """Main admin menu keyboard - Reply keyboard"""
    builder = ReplyKeyboardBuilder()
    
    # Admin buttons (1 per row for readability)
    builder.add(KeyboardButton(text="➕ O'yinchoq qo'shish"))
    builder.add(KeyboardButton(text="📂 Kategoriya qo'shish"))
    builder.add(KeyboardButton(text="✏️ Kategoriyalarni tahrirlash"))
    builder.add(KeyboardButton(text="🗑️ Kategoriyani o'chirish"))
    builder.add(KeyboardButton(text="📞 Buyurtma kontaktlari"))
    builder.add(KeyboardButton(text="🏆 Bestseller boshqaruvi"))
    builder.add(KeyboardButton(text="🏬 Do'kon manzillari"))
    builder.add(KeyboardButton(text="📦 Katalogni ko'rish"))
    builder.add(KeyboardButton(text="📊 Statistika"))
    builder.add(KeyboardButton(text="📊 Sotuv statistikasi"))
    builder.add(KeyboardButton(text="📣 Reklama yuborish"))
    builder.add(KeyboardButton(text="🏠 Bosh menyu"))
    
    builder.adjust(1)  # 1 button per row
    return builder.as_markup(resize_keyboard=True)


def get_admin_categories_keyboard(categories: list) -> ReplyKeyboardMarkup:
    """
    Admin categories keyboard for management
    
    Args:
        categories: List of Category objects
    """
    builder = ReplyKeyboardBuilder()
    
    # Add category buttons
    for category in categories:
        status = "✅" if category.is_active else "❌"
        builder.add(KeyboardButton(text=f"{status} {category.name}"))
    
    # Add back button
    builder.add(KeyboardButton(text="⬅️ Orqaga"))
    builder.add(KeyboardButton(text="🏠 Admin menyu"))
    
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


def get_admin_toy_pagination_keyboard(page: int, total_pages: int, toy_id: int, category_id: int = None) -> InlineKeyboardMarkup:
    """
    Admin toy pagination keyboard - Inline keyboard
    
    Args:
        page: Current page number
        total_pages: Total number of pages
        toy_id: Current toy ID
        category_id: Category ID for pagination
    """
    builder = InlineKeyboardBuilder()
    
    # Navigation buttons (max 2 per row)
    nav_buttons = []
    if page > 1:
        if category_id:
            nav_buttons.append(InlineKeyboardButton(
                text="⬅️ Oldingi",
                callback_data=f"admin_toy_page_{category_id}_{page - 1}"
            ))
        else:
            nav_buttons.append(InlineKeyboardButton(
                text="⬅️ Oldingi",
                callback_data=f"admin_toy_page_all_{page - 1}"
            ))
    if page < total_pages:
        if category_id:
            nav_buttons.append(InlineKeyboardButton(
                text="Keyingi ➡️",
                callback_data=f"admin_toy_page_{category_id}_{page + 1}"
            ))
        else:
            nav_buttons.append(InlineKeyboardButton(
                text="Keyingi ➡️",
                callback_data=f"admin_toy_page_all_{page + 1}"
            ))
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    # Manage toy button
    builder.add(InlineKeyboardButton(
        text="⚙️ Boshqarish",
        callback_data=f"admin_manage_{toy_id}"
    ))
    
    return builder.as_markup()


def get_admin_toy_manage_keyboard(toy_id: int, is_active: bool) -> InlineKeyboardMarkup:
    """
    Admin toy management keyboard - Inline keyboard
    
    Args:
        toy_id: Toy ID
        is_active: Whether toy is active
    """
    builder = InlineKeyboardBuilder()
    
    # Toggle status button
    status_text = "❌ O'chirish" if is_active else "✅ Yoqish"
    builder.add(InlineKeyboardButton(
        text=status_text,
        callback_data=f"admin_toggle_{toy_id}"
    ))
    
    # Edit button
    builder.add(InlineKeyboardButton(
        text="✏️ Tahrirlash",
        callback_data=f"admin_edit_{toy_id}"
    ))
    
    # Delete button
    builder.add(InlineKeyboardButton(
        text="🗑️ O'chirish",
        callback_data=f"admin_delete_{toy_id}"
    ))
    
    # Back button
    builder.add(InlineKeyboardButton(
        text="⬅️ Orqaga",
        callback_data="admin_back_catalog"
    ))
    
    return builder.as_markup()


def get_confirm_delete_keyboard(toy_id: int) -> InlineKeyboardMarkup:
    """Confirm delete keyboard - Inline keyboard"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="✅ Ha, o'chirish",
        callback_data=f"admin_confirm_delete_{toy_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="❌ Bekor qilish",
        callback_data=f"admin_manage_{toy_id}"
    ))
    return builder.as_markup()


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Cancel operation keyboard - Reply keyboard"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="❌ Bekor qilish"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


def get_media_done_keyboard() -> ReplyKeyboardMarkup:
    """Media collection done keyboard - Reply keyboard with Done button"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="✅ Tugatish"))
    builder.add(KeyboardButton(text="❌ Bekor qilish"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)
