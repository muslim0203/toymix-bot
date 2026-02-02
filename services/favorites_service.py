"""
Service for managing user favorites
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from database.models import Favorite


class FavoritesService:
    """Service for favorites operations"""
    
    @staticmethod
    def get_user_favorites(db: Session, user_id: int) -> List[Favorite]:
        """Get all favorites for a user"""
        return db.query(Favorite).filter(
            Favorite.user_id == user_id
        ).order_by(Favorite.created_at.desc()).all()
    
    @staticmethod
    def get_favorite(db: Session, user_id: int, toy_id: int) -> Optional[Favorite]:
        """Check if toy is in favorites"""
        return db.query(Favorite).filter(
            and_(
                Favorite.user_id == user_id,
                Favorite.toy_id == toy_id
            )
        ).first()
    
    @staticmethod
    def add_to_favorites(
        db: Session,
        user_id: int,
        toy_id: int,
        toy_name: str
    ) -> tuple[Favorite, bool]:
        """
        Add toy to favorites
        
        Args:
            db: Database session
            user_id: User ID
            toy_id: Toy ID
            toy_name: Toy name (denormalized)
            
        Returns:
            Tuple of (Favorite object, is_new: bool)
        """
        # Check if already exists
        existing = FavoritesService.get_favorite(db, user_id, toy_id)
        
        if existing:
            return (existing, False)  # Already exists
        
        # Create new favorite
        favorite = Favorite(
            user_id=user_id,
            toy_id=toy_id,
            toy_name=toy_name
        )
        db.add(favorite)
        db.commit()
        db.refresh(favorite)
        return (favorite, True)
    
    @staticmethod
    def remove_from_favorites(db: Session, user_id: int, toy_id: int) -> bool:
        """
        Remove toy from favorites
        
        Args:
            db: Database session
            user_id: User ID
            toy_id: Toy ID
            
        Returns:
            True if successful
        """
        favorite = FavoritesService.get_favorite(db, user_id, toy_id)
        
        if not favorite:
            return False
        
        db.delete(favorite)
        db.commit()
        return True
