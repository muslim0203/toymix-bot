"""
User handlers for shopping cart
"""
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery

from keyboards.user_kb import get_main_menu_keyboard
from keyboards.cart_kb import get_cart_actions_keyboard
from keyboards.toy_inline_kb import get_toy_actions_keyboard
from services.cart_service import CartService
from services.catalog_service import CatalogService
from services.favorites_service import FavoritesService
from services.order_contact_service import OrderContactService
from database.db import get_db_session

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text == "🛒 Savatcha")
async def show_cart(message: Message):
    """Show user's shopping cart"""
    user_id = message.from_user.id
    
    db = get_db_session()
    try:
        cart_items = CartService.get_user_cart(db, user_id)
        cart_text = CartService.format_cart_for_display(cart_items)
        
        if cart_items:
            await message.answer(
                cart_text,
                parse_mode="HTML",
                reply_markup=get_cart_actions_keyboard()
            )
        else:
            await message.answer(
                cart_text,
                reply_markup=get_main_menu_keyboard()
            )
        
    except Exception as e:
        logger.error(f"Error showing cart: {e}", exc_info=True)
        await message.answer(
            "❌ Xatolik yuz berdi.",
            reply_markup=get_main_menu_keyboard()
        )
    finally:
        db.close()


@router.callback_query(F.data.startswith("add_to_cart_"))
async def add_to_cart(callback: CallbackQuery):
    """Add toy to cart"""
    try:
        toy_id = int(callback.data.split("_")[-1])
        user_id = callback.from_user.id
        
        db = get_db_session()
        try:
            toy = CatalogService.get_toy_by_id(db, toy_id)
            if not toy or not toy.is_active:
                await callback.answer("❌ Bu o'yinchoq topilmadi", show_alert=True)
                return
            
            # Add to cart
            cart_item = CartService.add_to_cart(
                db,
                user_id=user_id,
                toy_id=toy_id,
                toy_name=toy.title,
                price=toy.price
            )
            
            await callback.answer("✅ O'yinchoq savatchaga qo'shildi!")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error adding to cart: {e}", exc_info=True)
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)


@router.callback_query(F.data.startswith("remove_from_cart_"))
async def remove_from_cart(callback: CallbackQuery):
    """Remove item from cart"""
    try:
        cart_item_id = int(callback.data.split("_")[-1])
        user_id = callback.from_user.id
        
        db = get_db_session()
        try:
            success = CartService.remove_from_cart(db, cart_item_id, user_id)
            
            if success:
                # Refresh cart view
                cart_items = CartService.get_user_cart(db, user_id)
                cart_text = CartService.format_cart_for_display(cart_items)
                
                if cart_items:
                    from keyboards.cart_kb import get_cart_actions_keyboard
                    await callback.message.edit_text(
                        cart_text,
                        parse_mode="HTML",
                        reply_markup=get_cart_actions_keyboard()
                    )
                else:
                    await callback.message.edit_text(
                        cart_text,
                        parse_mode="HTML"
                    )
                
                await callback.answer("✅ O'chirildi")
            else:
                await callback.answer("❌ Xatolik", show_alert=True)
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error removing from cart: {e}", exc_info=True)
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)


@router.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery):
    """Clear entire cart"""
    try:
        user_id = callback.from_user.id
        
        db = get_db_session()
        try:
            count = CartService.clear_cart(db, user_id)
            
            if count > 0:
                await callback.message.edit_text(
                    f"🗑️ Savatcha tozalandi!\n\n"
                    f"❌ Savatcha bo'sh",
                    parse_mode="HTML"
                )
                await callback.answer(f"✅ {count} ta o'yinchoq o'chirildi")
            else:
                await callback.answer("ℹ️ Savatcha allaqachon bo'sh", show_alert=True)
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error clearing cart: {e}", exc_info=True)
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)


@router.callback_query(F.data == "order_from_cart")
async def order_from_cart(callback: CallbackQuery):
    """Proceed to order from cart"""
    try:
        user_id = callback.from_user.id
        
        db = get_db_session()
        try:
            cart_items = CartService.get_user_cart(db, user_id)
            
            if not cart_items:
                await callback.answer("❌ Savatcha bo'sh", show_alert=True)
                return
            
            # Get contacts
            contacts = OrderContactService.get_active_contacts(db)
            contact_text = OrderContactService.format_contacts_for_display(contacts)
            
            # Format cart summary
            cart_text = CartService.format_cart_for_display(cart_items)
            
            order_text = (
                f"🛒 <b>Buyurtma berish</b>\n\n"
                f"{cart_text}\n\n"
                f"{contact_text}\n\n"
                f"Tez orada siz bilan bog'lanamiz! 😊"
            )
            
            # Try to edit message, if fails (media message), send new message
            try:
                if callback.message.photo or callback.message.video:
                    # If message has media, send new text message
                    await callback.message.answer(
                        order_text,
                        parse_mode="HTML"
                    )
                else:
                    # If text message, edit it
                    await callback.message.edit_text(
                        order_text,
                        parse_mode="HTML"
                    )
            except Exception as edit_error:
                # If edit fails, send new message
                logger.warning(f"Could not edit message, sending new: {edit_error}")
                await callback.message.answer(
                    order_text,
                    parse_mode="HTML"
                )
            
            await callback.answer("✅ Buyurtma qabul qilindi!")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error ordering from cart: {e}", exc_info=True)
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
