"""
Service for selecting random toys by category for advertisements
"""
import logging
from typing import List, Optional, Tuple
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from database.models import Toy, Category, DailyAdsLog

logger = logging.getLogger(__name__)


class AdsSelector:
    """Service for selecting toys for advertisements"""
    
    @staticmethod
    def get_active_categories(db: Session) -> List[Category]:
        """Get all active categories"""
        return db.query(Category).filter(Category.is_active == True).order_by(Category.name).all()
    
    @staticmethod
    def get_random_toy_from_category(
        db: Session, 
        category_id: int, 
        exclude_today: bool = True
    ) -> Optional[Toy]:
        """
        Get random active toy from specific category
        
        Args:
            db: Database session
            category_id: Category ID
            exclude_today: If True, exclude toys already posted today
            
        Returns:
            Random toy or None
        """
        today = date.today().isoformat()
        
        # Build query
        query = db.query(Toy).filter(
            Toy.is_active == True,
            Toy.category_id == category_id
        )
        
        # Exclude toys posted today
        if exclude_today:
            posted_today_ids = db.query(DailyAdsLog.toy_id).filter(
                DailyAdsLog.posted_date == today
            ).subquery()
            query = query.filter(~Toy.id.in_(db.query(posted_today_ids.c.toy_id)))
        
        # Get random toy
        toy = query.order_by(func.random()).first()
        
        return toy
    
    @staticmethod
    def get_random_category_toy_pair(
        db: Session,
        exclude_today: bool = True
    ) -> Optional[Tuple[Category, Toy]]:
        """
        Get random category and toy from that category
        
        Args:
            db: Database session
            exclude_today: If True, exclude toys already posted today
            
        Returns:
            Tuple of (Category, Toy) or None
        """
        # Get all active categories
        categories = AdsSelector.get_active_categories(db)
        
        if not categories:
            logger.warning("No active categories found")
            return None
        
        # Shuffle categories
        import random
        random.shuffle(categories)
        
        # Try each category until we find one with available toys
        for category in categories:
            toy = AdsSelector.get_random_toy_from_category(
                db,
                category_id=category.id,
                exclude_today=exclude_today
            )
            
            if toy:
                return (category, toy)
        
        # No toys available in any category
        logger.warning("No available toys found in any category")
        return None
    
    @staticmethod
    def log_ad_posted(
        db: Session,
        toy_id: int,
        category_id: Optional[int] = None
    ) -> None:
        """
        Log that an ad was posted
        
        Args:
            db: Database session
            toy_id: Toy ID that was posted
            category_id: Category ID (optional)
        """
        today = date.today().isoformat()
        ad_log = DailyAdsLog(
            toy_id=toy_id,
            category_id=category_id,
            posted_date=today
        )
        db.add(ad_log)
        db.commit()
    
    @staticmethod
    def get_today_posted_count(db: Session) -> int:
        """Get count of ads posted today"""
        today = date.today().isoformat()
        return db.query(DailyAdsLog).filter(DailyAdsLog.posted_date == today).count()
