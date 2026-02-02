"""
Scheduler for automatic bestseller generation
"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from services.bestseller_generator import BestsellerGenerator
from database.db import get_db_session

logger = logging.getLogger(__name__)


class BestsellerScheduler:
    """Scheduler for automatic bestseller generation"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
    
    async def generate_weekly_bestsellers(self):
        """Generate weekly bestsellers (every Monday 00:05)"""
        db = get_db_session()
        try:
            bestsellers = BestsellerGenerator.generate_auto_bestsellers(db, "weekly")
            logger.info(f"Generated {len(bestsellers)} weekly bestsellers")
        except Exception as e:
            logger.error(f"Error generating weekly bestsellers: {e}", exc_info=True)
        finally:
            db.close()
    
    async def generate_monthly_bestsellers(self):
        """Generate monthly bestsellers (1st day of month)"""
        db = get_db_session()
        try:
            bestsellers = BestsellerGenerator.generate_auto_bestsellers(db, "monthly")
            logger.info(f"Generated {len(bestsellers)} monthly bestsellers")
        except Exception as e:
            logger.error(f"Error generating monthly bestsellers: {e}", exc_info=True)
        finally:
            db.close()
    
    async def generate_yearly_bestsellers(self):
        """Generate yearly bestsellers (January 1st)"""
        db = get_db_session()
        try:
            bestsellers = BestsellerGenerator.generate_auto_bestsellers(db, "yearly")
            logger.info(f"Generated {len(bestsellers)} yearly bestsellers")
        except Exception as e:
            logger.error(f"Error generating yearly bestsellers: {e}", exc_info=True)
        finally:
            db.close()
    
    def start(self):
        """Start the scheduler"""
        if self.is_running:
            logger.warning("Bestseller scheduler is already running")
            return
        
        # Weekly: Every Monday at 00:05
        self.scheduler.add_job(
            self.generate_weekly_bestsellers,
            trigger=CronTrigger(day_of_week=0, hour=0, minute=5),
            id="generate_weekly_bestsellers",
            replace_existing=True
        )
        
        # Monthly: 1st day of month at 00:05
        self.scheduler.add_job(
            self.generate_monthly_bestsellers,
            trigger=CronTrigger(day=1, hour=0, minute=5),
            id="generate_monthly_bestsellers",
            replace_existing=True
        )
        
        # Yearly: January 1st at 00:05
        self.scheduler.add_job(
            self.generate_yearly_bestsellers,
            trigger=CronTrigger(month=1, day=1, hour=0, minute=5),
            id="generate_yearly_bestsellers",
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_running = True
        logger.info("✅ Bestseller scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            return
        
        self.scheduler.shutdown()
        self.is_running = False
        logger.info("Bestseller scheduler stopped")
