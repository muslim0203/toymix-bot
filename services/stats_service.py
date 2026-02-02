"""
Service for sales statistics and analytics
"""
import logging
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract

from database.models import SalesLog

logger = logging.getLogger(__name__)


class StatsService:
    """Service for sales statistics"""
    
    @staticmethod
    def log_sale_lead(
        db: Session,
        user_id: int,
        toy_id: int,
        toy_name: str,
        category_id: int = None,
        category_name: str = None
    ) -> None:
        """
        Log a sale lead when user clicks Buyurtma berish
        
        Args:
            db: Database session
            user_id: Telegram user ID
            toy_id: Toy ID
            toy_name: Toy name (denormalized)
            category_id: Category ID (optional)
            category_name: Category name (optional, denormalized)
        """
        sales_log = SalesLog(
            user_id=user_id,
            toy_id=toy_id,
            toy_name=toy_name,
            category_id=category_id,
            category_name=category_name
        )
        db.add(sales_log)
        db.commit()
    
    @staticmethod
    def get_category_stats_by_time_range(
        db: Session,
        time_range: str  # 'weekly', 'monthly', 'yearly'
    ) -> List[Tuple[str, int]]:
        """
        Get category statistics for a time range
        
        Args:
            db: Database session
            time_range: 'weekly', 'monthly', or 'yearly'
            
        Returns:
            List of tuples (category_name, count) sorted by count descending
        """
        now = datetime.now()
        
        if time_range == 'weekly':
            # Last 7 days
            start_date = now - timedelta(days=7)
            query = db.query(
                SalesLog.category_name,
                func.count(SalesLog.id).label('count')
            ).filter(
                SalesLog.created_at >= start_date,
                SalesLog.category_name.isnot(None)
            ).group_by(
                SalesLog.category_name
            ).order_by(
                func.count(SalesLog.id).desc()
            )
        
        elif time_range == 'monthly':
            # Current month
            query = db.query(
                SalesLog.category_name,
                func.count(SalesLog.id).label('count')
            ).filter(
                extract('year', SalesLog.created_at) == now.year,
                extract('month', SalesLog.created_at) == now.month,
                SalesLog.category_name.isnot(None)
            ).group_by(
                SalesLog.category_name
            ).order_by(
                func.count(SalesLog.id).desc()
            )
        
        elif time_range == 'yearly':
            # Current year
            query = db.query(
                SalesLog.category_name,
                func.count(SalesLog.id).label('count')
            ).filter(
                extract('year', SalesLog.created_at) == now.year,
                SalesLog.category_name.isnot(None)
            ).group_by(
                SalesLog.category_name
            ).order_by(
                func.count(SalesLog.id).desc()
            )
        
        else:
            return []
        
        results = query.all()
        return [(row.category_name, row.count) for row in results]
    
    @staticmethod
    def get_toy_stats_by_time_range(
        db: Session,
        time_range: str  # 'weekly', 'monthly', 'yearly'
    ) -> List[Tuple[str, int]]:
        """
        Get toy statistics for a time range
        
        Args:
            db: Database session
            time_range: 'weekly', 'monthly', or 'yearly'
            
        Returns:
            List of tuples (toy_name, count) sorted by count descending
        """
        now = datetime.now()
        
        if time_range == 'weekly':
            # Last 7 days
            start_date = now - timedelta(days=7)
            query = db.query(
                SalesLog.toy_name,
                func.count(SalesLog.id).label('count')
            ).filter(
                SalesLog.created_at >= start_date
            ).group_by(
                SalesLog.toy_name
            ).order_by(
                func.count(SalesLog.id).desc()
            )
        
        elif time_range == 'monthly':
            # Current month
            query = db.query(
                SalesLog.toy_name,
                func.count(SalesLog.id).label('count')
            ).filter(
                extract('year', SalesLog.created_at) == now.year,
                extract('month', SalesLog.created_at) == now.month
            ).group_by(
                SalesLog.toy_name
            ).order_by(
                func.count(SalesLog.id).desc()
            )
        
        elif time_range == 'yearly':
            # Current year
            query = db.query(
                SalesLog.toy_name,
                func.count(SalesLog.id).label('count')
            ).filter(
                extract('year', SalesLog.created_at) == now.year
            ).group_by(
                SalesLog.toy_name
            ).order_by(
                func.count(SalesLog.id).desc()
            )
        
        else:
            return []
        
        results = query.all()
        return [(row.toy_name, row.count) for row in results]
    
    @staticmethod
    def format_category_stats(stats: List[Tuple[str, int]], time_range: str) -> str:
        """
        Format category statistics for display
        
        Args:
            stats: List of (category_name, count) tuples
            time_range: 'weekly', 'monthly', or 'yearly'
            
        Returns:
            Formatted string in Uzbek
        """
        if not stats:
            return "❌ Ushbu davrda ma'lumot mavjud emas"
        
        time_range_text = {
            'weekly': 'Haftalik',
            'monthly': 'Oylik',
            'yearly': 'Yillik'
        }.get(time_range, '')
        
        text = f"📊 {time_range_text} sotuv statistikasi (kategoriya bo'yicha):\n\n"
        
        for idx, (category_name, count) in enumerate(stats, 1):
            emoji = "🧸"  # Default emoji, can be customized
            text += f"{idx}️⃣ {emoji} {category_name} — {count} ta\n"
        
        return text
    
    @staticmethod
    def format_toy_stats(stats: List[Tuple[str, int]], time_range: str) -> str:
        """
        Format toy statistics for display
        
        Args:
            stats: List of (toy_name, count) tuples
            time_range: 'weekly', 'monthly', or 'yearly'
            
        Returns:
            Formatted string in Uzbek
        """
        if not stats:
            return "❌ Ushbu davrda ma'lumot mavjud emas"
        
        time_range_text = {
            'weekly': 'Haftalik',
            'monthly': 'Oylik',
            'yearly': 'Yillik'
        }.get(time_range, '')
        
        text = f"📊 {time_range_text} sotuv statistikasi (o'yinchoq bo'yicha):\n\n"
        
        for idx, (toy_name, count) in enumerate(stats, 1):
            text += f"{idx}️⃣ {toy_name} — {count} ta\n"
        
        return text
