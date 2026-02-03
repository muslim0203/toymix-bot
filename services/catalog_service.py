"""
Catalog service for managing toys
"""
from typing import List, Optional, Tuple
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from database.models import Toy, DailyAd
from config import ITEMS_PER_PAGE


class CatalogService:
    """Service for catalog operations"""
    
    @staticmethod
    def get_active_toys_by_category(db: Session, category_id: int, page: int = 0, page_size: int = 10) -> Tuple[List[Toy], int]:
        """
        Get paginated list of active toys by category
        
        Args:
            db: Database session
            category_id: Category ID
            page: Page number (0-indexed)
            page_size: Number of items per page (default: 10)
            
        Returns:
            Tuple of (toys list, total count)
        """
        # Calculate offset
        offset = page * page_size
        
        # Get total count
        total_count = db.query(Toy).filter(
            Toy.is_active == True,
            Toy.category_id == category_id
        ).count()
        
        # Get paginated toys
        toys = db.query(Toy).filter(
            Toy.is_active == True,
            Toy.category_id == category_id
        ).order_by(
            Toy.created_at.desc()  # Newest first
        ).offset(offset).limit(page_size).all()  # Use offset and limit for pagination
        
        return toys, total_count
    
    @staticmethod
    def get_all_active_toys_by_category(db: Session, category_id: int) -> List[Toy]:
        """
        Get ALL active toys by category (no pagination)
        
        Args:
            db: Database session
            category_id: Category ID
            
        Returns:
            List of all active toys in the category
        """
        toys = db.query(Toy).filter(
            Toy.is_active == True,
            Toy.category_id == category_id
        ).order_by(
            Toy.created_at.desc()
        ).all()  # Always use .all() to get all products
        
        return toys
    
    @staticmethod
    def get_active_toys(db: Session, page: int = 1) -> Tuple[List[Toy], int]:
        """
        Get paginated list of active toys (all categories)
        
        Args:
            db: Database session
            page: Page number (1-indexed)
            
        Returns:
            Tuple of (toys list, total pages)
        """
        offset = (page - 1) * ITEMS_PER_PAGE
        
        # Get total count
        total_count = db.query(Toy).filter(Toy.is_active == True).count()
        total_pages = (total_count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE if total_count > 0 else 1
        
        # Get toys for current page
        toys = db.query(Toy).filter(
            Toy.is_active == True
        ).order_by(
            Toy.created_at.desc()
        ).offset(offset).limit(ITEMS_PER_PAGE).all()
        
        return toys, total_pages
    
    @staticmethod
    def get_all_toys(db: Session, page: int = 1) -> Tuple[List[Toy], int]:
        """
        Get paginated list of all toys (including inactive)
        
        Args:
            db: Database session
            page: Page number (1-indexed)
            
        Returns:
            Tuple of (toys list, total pages)
        """
        offset = (page - 1) * ITEMS_PER_PAGE
        
        # Get total count
        total_count = db.query(Toy).count()
        total_pages = (total_count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE if total_count > 0 else 1
        
        # Get toys for current page
        toys = db.query(Toy).order_by(
            Toy.created_at.desc()
        ).offset(offset).limit(ITEMS_PER_PAGE).all()
        
        return toys, total_pages
    
    @staticmethod
    def get_toy_by_id(db: Session, toy_id: int) -> Optional[Toy]:
        """Get toy by ID"""
        return db.query(Toy).filter(Toy.id == toy_id).first()
    
    @staticmethod
    def create_toy(
        db: Session,
        title: str,
        price: str,
        description: str,
        media_type: str,
        media_file_id: str,
        category_id: Optional[int] = None
    ) -> Toy:
        """
        Create a new toy
        
        IMPORTANT: This always creates a NEW row.
        It NEVER updates or deletes existing toys.
        Multiple toys can have the same category_id.
        
        Args:
            db: Database session
            title: Toy title
            price: Toy price
            description: Toy description
            media_type: Media type (deprecated, for backward compatibility)
            media_file_id: Media file ID (deprecated, for backward compatibility)
            category_id: Category ID (optional)
            
        Returns:
            Newly created Toy object
        """
        # Always create a new toy instance
        # This ensures we never overwrite existing products
        toy = Toy(
            title=title,
            price=price,
            description=description,
            media_type=media_type,
            media_file_id=media_file_id,
            category_id=category_id,
            is_active=True
        )
        
        # Add to session (this creates a new row)
        db.add(toy)
        db.commit()
        db.refresh(toy)
        
        return toy
    
    @staticmethod
    def update_toy(
        db: Session,
        toy_id: int,
        title: Optional[str] = None,
        price: Optional[str] = None,
        description: Optional[str] = None,
        media_type: Optional[str] = None,
        media_file_id: Optional[str] = None,
        category_id: Optional[int] = None
    ) -> Optional[Toy]:
        """Update toy fields"""
        toy = CatalogService.get_toy_by_id(db, toy_id)
        if not toy:
            return None
        
        if title is not None:
            toy.title = title
        if price is not None:
            toy.price = price
        if description is not None:
            toy.description = description
        if media_type is not None:
            toy.media_type = media_type
        if media_file_id is not None:
            toy.media_file_id = media_file_id
        if category_id is not None:
            toy.category_id = category_id
        
        toy.updated_at = datetime.now()
        db.commit()
        db.refresh(toy)
        return toy
    
    @staticmethod
    def toggle_toy_active(db: Session, toy_id: int) -> Optional[Toy]:
        """Toggle toy active status"""
        toy = CatalogService.get_toy_by_id(db, toy_id)
        if not toy:
            return None
        
        toy.is_active = not toy.is_active
        toy.updated_at = datetime.now()
        db.commit()
        db.refresh(toy)
        return toy
    
    @staticmethod
    def delete_toy(db: Session, toy_id: int) -> bool:
        """Delete a toy"""
        toy = CatalogService.get_toy_by_id(db, toy_id)
        if not toy:
            return False
        
        db.delete(toy)
        db.commit()
        return True
    
    @staticmethod
    def get_stats(db: Session) -> dict:
        """Get catalog statistics"""
        total_toys = db.query(Toy).count()
        active_toys = db.query(Toy).filter(Toy.is_active == True).count()
        inactive_toys = total_toys - active_toys
        
        return {
            "total": total_toys,
            "active": active_toys,
            "inactive": inactive_toys
        }
    
    @staticmethod
    def get_random_active_toys_for_ad(db: Session, count: int, exclude_today: bool = True) -> List[Toy]:
        """
        Get random active toys for advertisement
        
        Args:
            db: Database session
            count: Number of toys to get
            exclude_today: If True, exclude toys already posted today
            
        Returns:
            List of random active toys
        """
        today = date.today().isoformat()
        
        # Get active toys
        query = db.query(Toy).filter(Toy.is_active == True)
        
        # Exclude toys posted today
        if exclude_today:
            posted_today_ids = db.query(DailyAd.toy_id).filter(
                DailyAd.posted_date == today
            ).subquery()
            query = query.filter(~Toy.id.in_(db.query(posted_today_ids.c.toy_id)))
        
        # Get random toys
        toys = query.order_by(func.random()).limit(count).all()
        
        return toys
    
    @staticmethod
    def mark_toy_posted(db: Session, toy_id: int) -> None:
        """Mark a toy as posted today"""
        today = date.today().isoformat()
        ad_record = DailyAd(
            toy_id=toy_id,
            posted_date=today
        )
        db.add(ad_record)
        db.commit()
