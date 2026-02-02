"""
Service for generating and managing bestseller categories
"""
import logging
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_

from database.models import SalesLog, BestsellerCategory, Category
from services.stats_service import StatsService

logger = logging.getLogger(__name__)


class BestsellerGenerator:
    """Service for bestseller category generation and management"""
    
    @staticmethod
    def generate_auto_bestsellers(
        db: Session,
        period: str  # 'weekly', 'monthly', 'yearly'
    ) -> List[BestsellerCategory]:
        """
        Generate automatic bestseller categories from sales logs
        
        Args:
            db: Database session
            period: 'weekly', 'monthly', or 'yearly'
            
        Returns:
            List of created BestsellerCategory objects
        """
        # First, deactivate previous auto records for this period
        db.query(BestsellerCategory).filter(
            BestsellerCategory.period == period,
            BestsellerCategory.source == "auto",
            BestsellerCategory.is_active == True
        ).update({BestsellerCategory.is_active: False})
        db.commit()
        
        # Get category stats for the period
        stats = StatsService.get_category_stats_by_time_range(db, period)
        
        if not stats or len(stats) == 0:
            logger.warning(f"No stats available for {period} period")
            return []
        
        # Take TOP-5
        top_5 = stats[:5]
        
        # Create bestseller records
        bestsellers = []
        for rank, (category_name, count) in enumerate(top_5, 1):
            # Get category by name
            category = db.query(Category).filter(Category.name == category_name).first()
            if not category:
                logger.warning(f"Category '{category_name}' not found in database")
                continue
            
            # Check if manual bestseller exists at this rank
            existing_manual = db.query(BestsellerCategory).filter(
                BestsellerCategory.period == period,
                BestsellerCategory.rank == rank,
                BestsellerCategory.source == "manual",
                BestsellerCategory.is_active == True
            ).first()
            
            # Skip if manual exists at this rank
            if existing_manual:
                logger.info(f"Skipping rank {rank} - manual bestseller exists")
                continue
            
            bestseller = BestsellerCategory(
                category_id=category.id,
                category_name=category_name,
                source="auto",
                period=period,
                rank=rank,
                is_active=True
            )
            db.add(bestseller)
            bestsellers.append(bestseller)
        
        db.commit()
        logger.info(f"Generated {len(bestsellers)} auto bestsellers for {period} period")
        return bestsellers
    
    @staticmethod
    def get_bestsellers(
        db: Session,
        period: str,
        limit: int = 5
    ) -> List[BestsellerCategory]:
        """
        Get bestseller categories for a period (manual + auto)
        
        Args:
            db: Database session
            period: 'weekly', 'monthly', or 'yearly'
            limit: Maximum number to return (default 5)
            
        Returns:
            List of BestsellerCategory sorted by rank
        """
        # Get all active bestsellers for period
        bestsellers = db.query(BestsellerCategory).filter(
            BestsellerCategory.period == period,
            BestsellerCategory.is_active == True
        ).order_by(BestsellerCategory.rank).limit(limit).all()
        
        return bestsellers
    
    @staticmethod
    def create_manual_bestseller(
        db: Session,
        category_id: int,
        period: str,
        rank: int
    ) -> Optional[BestsellerCategory]:
        """
        Create manual bestseller category
        
        Args:
            db: Database session
            category_id: Category ID
            period: 'weekly', 'monthly', or 'yearly'
            rank: Rank (1-5)
            
        Returns:
            Created BestsellerCategory or None
        """
        # Validate rank
        if rank < 1 or rank > 5:
            return None
        
        # Get category
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            return None
        
        # Check if rank is already taken by manual
        existing_manual = db.query(BestsellerCategory).filter(
            BestsellerCategory.period == period,
            BestsellerCategory.rank == rank,
            BestsellerCategory.source == "manual",
            BestsellerCategory.is_active == True
        ).first()
        
        if existing_manual:
            # Update existing
            existing_manual.category_id = category_id
            existing_manual.category_name = category.name
            db.commit()
            db.refresh(existing_manual)
            return existing_manual
        
        # Deactivate auto bestseller at this rank
        db.query(BestsellerCategory).filter(
            BestsellerCategory.period == period,
            BestsellerCategory.rank == rank,
            BestsellerCategory.source == "auto",
            BestsellerCategory.is_active == True
        ).update({BestsellerCategory.is_active: False})
        
        # Create new manual bestseller
        bestseller = BestsellerCategory(
            category_id=category_id,
            category_name=category.name,
            source="manual",
            period=period,
            rank=rank,
            is_active=True
        )
        db.add(bestseller)
        db.commit()
        db.refresh(bestseller)
        
        return bestseller
    
    @staticmethod
    def deactivate_bestseller(
        db: Session,
        bestseller_id: int
    ) -> bool:
        """
        Deactivate a bestseller (soft delete)
        
        Args:
            db: Database session
            bestseller_id: Bestseller ID
            
        Returns:
            True if successful
        """
        bestseller = db.query(BestsellerCategory).filter(
            BestsellerCategory.id == bestseller_id
        ).first()
        
        if not bestseller:
            return False
        
        bestseller.is_active = False
        db.commit()
        return True
    
    @staticmethod
    def format_bestsellers_for_display(
        bestsellers: List[BestsellerCategory],
        period: str
    ) -> str:
        """
        Format bestseller list for user display
        
        Args:
            bestsellers: List of BestsellerCategory objects
            period: Period name
            
        Returns:
            Formatted string in Uzbek
        """
        if not bestsellers:
            return "❌ Ushbu davrda bestseller kategoriyalar mavjud emas"
        
        period_text = {
            'weekly': 'Haftalik',
            'monthly': 'Oylik',
            'yearly': 'Yillik'
        }.get(period, period)
        
        text = f"🏆 {period_text} Bestseller TOP-5 (kategoriya):\n\n"
        
        medals = {
            1: "🥇",
            2: "🥈",
            3: "🥉"
        }
        
        for bestseller in bestsellers:
            emoji = medals.get(bestseller.rank, f"{bestseller.rank}️⃣")
            text += f"{emoji} {bestseller.category_name}\n"
        
        return text
