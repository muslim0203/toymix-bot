"""
Service for formatting advertisement messages with professional design
"""
from typing import Optional
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from config import BOT_USERNAME, GROUP_LINK, ORDER_PHONE
from database.models import Toy, Category


class AdsFormatter:
    """Service for formatting advertisement messages"""
    
    @staticmethod
    def format_ad_message(toy: Toy, category: Optional[Category] = None) -> str:
        """
        Format advertisement message with professional design
        
        Args:
            toy: Toy object
            category: Category object (optional)
            
        Returns:
            Formatted message text (Uzbek)
        """
        category_name = category.name if category else "Kategoriyasiz"
        
        message = (
            f"✨ Yangi taklif — bolalar uchun zo'r o'yinchoq!\n\n"
            f"🧸 Kategoriya: <b>{category_name}</b>\n"
            f"📦 Mahsulot: <b>{toy.title}</b>\n\n"
            f"💰 Narxi: {toy.price} so'm\n\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🛒 Buyurtma berish:\n"
            f"👉 Bot orqali: {BOT_USERNAME}\n"
            f"📞 Telefon: {ORDER_PHONE}\n"
            f"👥 Guruh: {GROUP_LINK}\n\n"
            f"🎁 Bolangizni quvontiring!"
        )
        
        return message
    
    @staticmethod
    def get_ad_keyboard(toy_id: int) -> InlineKeyboardMarkup:
        """
        Get inline keyboard for advertisement with CTA buttons
        
        Args:
            toy_id: Toy ID for order button
            
        Returns:
            InlineKeyboardMarkup with CTA buttons
        """
        builder = InlineKeyboardBuilder()
        
        # Row 1: Buyurtma bering - opens bot private chat
        # Format bot username for URL (remove @ if present)
        bot_username_clean = BOT_USERNAME.replace('@', '')
        builder.add(InlineKeyboardButton(
            text="🛒 Buyurtma bering",
            url=f"https://t.me/{bot_username_clean}?start=order_{toy_id}"
        ))
        
        # Row 2: Guruhga qo'shilish and Katalogni ko'rish
        builder.add(InlineKeyboardButton(
            text="👥 Guruhga qo'shilish",
            url=GROUP_LINK
        ))
        # Format bot username for URL (remove @ if present)
        bot_username_clean = BOT_USERNAME.replace('@', '')
        builder.add(InlineKeyboardButton(
            text="📦 Katalogni ko'rish",
            url=f"https://t.me/{bot_username_clean}?start=catalog"
        ))
        
        # Adjust: 1 button in first row, 2 buttons in second row
        builder.adjust(1, 2)
        
        return builder.as_markup()
