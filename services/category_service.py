"""
Category service for managing toy categories
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from database.models import Category, Toy
from config import ITEMS_PER_PAGE


class CategoryService:
    """Service for category operations"""
    
    @staticmethod
    def get_active_categories(db: Session) -> List[Category]:
        """Get all active categories"""
        return db.query(Category).filter(Category.is_active == True).order_by(Category.name).all()
    
    @staticmethod
    def get_all_categories(db: Session) -> List[Category]:
        """Get all categories (including inactive)"""
        return db.query(Category).order_by(Category.name).all()
    
    @staticmethod
    def get_category_by_id(db: Session, category_id: int) -> Optional[Category]:
        """Get category by ID"""
        return db.query(Category).filter(Category.id == category_id).first()
    
    @staticmethod
    def get_category_by_name(db: Session, name: str) -> Optional[Category]:
        """Get category by name"""
        return db.query(Category).filter(Category.name == name).first()
    
    @staticmethod
    def create_category(db: Session, name: str) -> Category:
        """Create a new category"""
        category = Category(name=name, is_active=True)
        db.add(category)
        db.commit()
        db.refresh(category)
        return category
    
    @staticmethod
    def update_category(db: Session, category_id: int, name: Optional[str] = None) -> Optional[Category]:
        """Update category"""
        category = CategoryService.get_category_by_id(db, category_id)
        if not category:
            return None
        
        if name is not None:
            category.name = name
        
        category.updated_at = datetime.now()
        db.commit()
        db.refresh(category)
        return category
    
    @staticmethod
    def toggle_category_active(db: Session, category_id: int) -> Optional[Category]:
        """Toggle category active status"""
        category = CategoryService.get_category_by_id(db, category_id)
        if not category:
            return None
        
        category.is_active = not category.is_active
        category.updated_at = datetime.now()
        db.commit()
        db.refresh(category)
        return category
    
    @staticmethod
    def delete_category(db: Session, category_id: int) -> bool:
        """Delete a category (toys will be set to category_id=None)"""
        category = CategoryService.get_category_by_id(db, category_id)
        if not category:
            return False
        
        # Set toys' category_id to None
        db.query(Toy).filter(Toy.category_id == category_id).update({Toy.category_id: None})
        
        db.delete(category)
        db.commit()
        return True
    
    @staticmethod
    def get_category_stats(db: Session) -> dict:
        """Get category statistics"""
        total_categories = db.query(Category).count()
        active_categories = db.query(Category).filter(Category.is_active == True).count()
        inactive_categories = total_categories - active_categories
        
        return {
            "total": total_categories,
            "active": active_categories,
            "inactive": inactive_categories
        }
