"""
Utility functions for random advertisement selection
"""
from datetime import date
from typing import List
from sqlalchemy.orm import Session

from database.models import Toy, DailyAd


def get_today_posted_toy_ids(db: Session) -> List[int]:
    """
    Get list of toy IDs that were posted today
    
    Args:
        db: Database session
        
    Returns:
        List of toy IDs
    """
    today = date.today().isoformat()
    posted_ids = db.query(DailyAd.toy_id).filter(
        DailyAd.posted_date == today
    ).all()
    return [toy_id[0] for toy_id in posted_ids]


def clear_old_daily_ads(db: Session, days_to_keep: int = 7):
    """
    Clean up old daily ad records (keep only last N days)
    
    Args:
        db: Database session
        days_to_keep: Number of days to keep records
    """
    from datetime import timedelta
    
    cutoff_date = (date.today() - timedelta(days=days_to_keep)).isoformat()
    deleted = db.query(DailyAd).filter(
        DailyAd.posted_date < cutoff_date
    ).delete()
    db.commit()
    return deleted
