"""
Service for managing shopping cart
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from database.models import CartItem, Toy


class CartService:
    """Service for cart operations"""
    
    @staticmethod
    def get_user_cart(db: Session, user_id: int) -> List[CartItem]:
        """Get all cart items for a user"""
        return db.query(CartItem).filter(
            CartItem.user_id == user_id
        ).order_by(CartItem.created_at).all()
    
    @staticmethod
    def get_cart_item(db: Session, user_id: int, toy_id: int) -> Optional[CartItem]:
        """Get specific cart item"""
        return db.query(CartItem).filter(
            and_(
                CartItem.user_id == user_id,
                CartItem.toy_id == toy_id
            )
        ).first()
    
    @staticmethod
    def add_to_cart(
        db: Session,
        user_id: int,
        toy_id: int,
        toy_name: str,
        price: str
    ) -> CartItem:
        """
        Add toy to cart or increase quantity if exists
        
        Args:
            db: Database session
            user_id: User ID
            toy_id: Toy ID
            toy_name: Toy name (denormalized)
            price: Toy price (denormalized)
            
        Returns:
            CartItem object
        """
        # Check if item already exists
        existing_item = CartService.get_cart_item(db, user_id, toy_id)
        
        if existing_item:
            # Increase quantity
            existing_item.quantity += 1
            db.commit()
            db.refresh(existing_item)
            return existing_item
        else:
            # Create new cart item
            cart_item = CartItem(
                user_id=user_id,
                toy_id=toy_id,
                toy_name=toy_name,
                price=price,
                quantity=1
            )
            db.add(cart_item)
            db.commit()
            db.refresh(cart_item)
            return cart_item
    
    @staticmethod
    def remove_from_cart(db: Session, cart_item_id: int, user_id: int) -> bool:
        """
        Remove item from cart
        
        Args:
            db: Database session
            cart_item_id: Cart item ID
            user_id: User ID (for security)
            
        Returns:
            True if successful
        """
        cart_item = db.query(CartItem).filter(
            and_(
                CartItem.id == cart_item_id,
                CartItem.user_id == user_id
            )
        ).first()
        
        if not cart_item:
            return False
        
        db.delete(cart_item)
        db.commit()
        return True
    
    @staticmethod
    def clear_cart(db: Session, user_id: int) -> int:
        """
        Clear all items from user's cart
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Number of items deleted
        """
        count = db.query(CartItem).filter(
            CartItem.user_id == user_id
        ).delete()
        db.commit()
        return count
    
    @staticmethod
    def calculate_total_price(cart_items: List[CartItem]) -> int:
        """
        Calculate total price of cart items
        
        Args:
            cart_items: List of CartItem objects
            
        Returns:
            Total price in so'm (as integer)
        """
        total = 0
        for item in cart_items:
            # Parse price string (remove "so'm", spaces, etc.)
            price_str = item.price.replace("so'm", "").replace(" ", "").replace(",", "").strip()
            try:
                price = int(price_str)
                total += price * item.quantity
            except ValueError:
                # If price can't be parsed, skip this item
                continue
        return total
    
    @staticmethod
    def format_cart_for_display(cart_items: List[CartItem]) -> str:
        """
        Format cart items for display
        
        Args:
            cart_items: List of CartItem objects
            
        Returns:
            Formatted string in Uzbek
        """
        if not cart_items:
            return "❌ Savatcha bo'sh"
        
        text = "🛒 <b>Sizning savatchingiz:</b>\n\n"
        
        for idx, item in enumerate(cart_items, 1):
            text += f"{idx}️⃣ {item.toy_name}\n"
            text += f"   💰 {item.price} × {item.quantity}\n\n"
        
        # Calculate total
        total = CartService.calculate_total_price(cart_items)
        total_formatted = f"{total:,}".replace(",", " ")
        
        text += "────────────────\n"
        text += f"💵 <b>Umumiy narx: {total_formatted} so'm</b>"
        
        return text
