"""
User handlers for favorites
"""
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery

from keyboards.user_kb import get_main_menu_keyboard
from keyboards.toy_inline_kb import get_favorite_toy_keyboard
from services.favorites_service import FavoritesService
from services.catalog_service import CatalogService
from database.db import get_db_session

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text == "❤️ Sevimlilar")
async def show_favorites(message: Message):
    """Show user's favorites"""
    user_id = message.from_user.id
    
    db = get_db_session()
    try:
        favorites = FavoritesService.get_user_favorites(db, user_id)
        
        if not favorites:
            await message.answer(
                "❌ Sevimlilar bo'sh\n\n"
                "O'yinchoqlarni sevimlilarga qo'shish uchun ❤️ tugmasini bosing.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        await message.answer(
            f"❤️ <b>Sizning sevimlilaringiz</b>\n\n"
            f"📦 {len(favorites)} ta o'yinchoq saqlangan",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )
        
        # Show each favorite toy
        for favorite in favorites:
            toy = CatalogService.get_toy_by_id(db, favorite.toy_id)
            if not toy or not toy.is_active:
                continue
            
            message_text = (
                f"📦 <b>{toy.title}</b>\n"
                f"💰 Narxi: {toy.price}\n\n"
                f"📝 {toy.description}"
            )
            
            if toy.media_type == "image":
                await message.answer_photo(
                    photo=toy.media_file_id,
                    caption=message_text,
                    parse_mode="HTML",
                    reply_markup=get_favorite_toy_keyboard(toy.id)
                )
            elif toy.media_type == "video":
                await message.answer_video(
                    video=toy.media_file_id,
                    caption=message_text,
                    parse_mode="HTML",
                    reply_markup=get_favorite_toy_keyboard(toy.id)
                )
        
    except Exception as e:
        logger.error(f"Error showing favorites: {e}", exc_info=True)
        await message.answer(
            "❌ Xatolik yuz berdi.",
            reply_markup=get_main_menu_keyboard()
        )
    finally:
        db.close()


@router.callback_query(F.data.startswith("add_to_favorites_"))
async def add_to_favorites(callback: CallbackQuery):
    """Add toy to favorites"""
    try:
        toy_id = int(callback.data.split("_")[-1])
        user_id = callback.from_user.id
        
        db = get_db_session()
        try:
            toy = CatalogService.get_toy_by_id(db, toy_id)
            if not toy or not toy.is_active:
                await callback.answer("❌ Bu o'yinchoq topilmadi", show_alert=True)
                return
            
            # Add to favorites
            favorite, is_new = FavoritesService.add_to_favorites(
                db,
                user_id=user_id,
                toy_id=toy_id,
                toy_name=toy.title
            )
            
            if is_new:
                await callback.answer("✅ Sevimlilarga qo'shildi!")
            else:
                await callback.answer("ℹ️ Bu o'yinchoq allaqachon sevimlilarda", show_alert=True)
            
            # Update button state - refresh the message with new keyboard
            # Note: We need to rebuild the full keyboard with pagination
            # For now, just show success message
            pass  # Button state will update on next view
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error adding to favorites: {e}", exc_info=True)
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)


@router.callback_query(F.data.startswith("remove_from_favorites_"))
async def remove_from_favorites(callback: CallbackQuery):
    """Remove toy from favorites"""
    try:
        toy_id = int(callback.data.split("_")[-1])
        user_id = callback.from_user.id
        
        db = get_db_session()
        try:
            success = FavoritesService.remove_from_favorites(db, user_id, toy_id)
            
            if success:
                await callback.answer("✅ Sevimlilardan o'chirildi")
                
                # Update button state if message still exists
                try:
                    from keyboards.toy_inline_kb import get_toy_actions_keyboard
                    await callback.message.edit_reply_markup(
                        reply_markup=get_toy_actions_keyboard(toy_id, is_favorite=False)
                    )
                except:
                    pass  # Message might be deleted or not editable
            else:
                await callback.answer("❌ Xatolik", show_alert=True)
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error removing from favorites: {e}", exc_info=True)
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
