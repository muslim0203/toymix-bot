"""
Scheduler service for automated group advertisements
"""
import logging
import random
from datetime import datetime, time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot
from sqlalchemy.orm import Session

from config import DAILY_AD_COUNT, AD_START_HOUR, AD_END_HOUR, GROUP_CHAT_ID
from services.catalog_service import CatalogService
from database.db import get_db_session

logger = logging.getLogger(__name__)


class AdScheduler:
    """Scheduler for automated toy advertisements"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
    
    async def post_random_ad(self):
        """
        Post a random toy advertisement to the group
        This function is called by the scheduler
        """
        try:
            if GROUP_CHAT_ID == 0:
                logger.warning("GROUP_CHAT_ID not configured, skipping ad post")
                return
            
            db = get_db_session()
            try:
                # Get random active toys (excluding today's posts)
                toys = CatalogService.get_random_active_toys_for_ad(
                    db, 
                    count=1, 
                    exclude_today=True
                )
                
                if not toys:
                    logger.info("No toys available for posting today")
                    return
                
                toy = toys[0]
                
                # Format advertisement message
                message_text = (
                    f"🎁 <b>{toy.title}</b>\n\n"
                    f"💰 Narxi: {toy.price}\n\n"
                    f"{toy.description}\n\n"
                    f"📦 Buyurtma berish uchun botga yozing: @{self.bot.username}"
                )
                
                # Send media with caption
                if toy.media_type == "image":
                    await self.bot.send_photo(
                        chat_id=GROUP_CHAT_ID,
                        photo=toy.media_file_id,
                        caption=message_text,
                        parse_mode="HTML"
                    )
                elif toy.media_type == "video":
                    await self.bot.send_video(
                        chat_id=GROUP_CHAT_ID,
                        video=toy.media_file_id,
                        caption=message_text,
                        parse_mode="HTML"
                    )
                
                # Mark toy as posted today
                CatalogService.mark_toy_posted(db, toy.id)
                
                logger.info(f"Posted ad for toy ID {toy.id} ({toy.title})")
                
            except Exception as e:
                logger.error(f"Error posting ad: {e}", exc_info=True)
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Critical error in post_random_ad: {e}", exc_info=True)
    
    def _generate_random_times(self, count: int) -> list:
        """
        Generate random times within the allowed window for posting ads
        
        Args:
            count: Number of random times to generate
            
        Returns:
            List of (hour, minute) tuples
        """
        times = []
        for _ in range(count):
            hour = random.randint(AD_START_HOUR, AD_END_HOUR - 1)
            minute = random.randint(0, 59)
            times.append((hour, minute))
        
        # Sort times
        times.sort()
        return times
    
    def start(self):
        """Start the scheduler"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        # Generate random posting times for today
        posting_times = self._generate_random_times(DAILY_AD_COUNT)
        
        # Schedule ads at random times
        for hour, minute in posting_times:
            trigger = CronTrigger(hour=hour, minute=minute)
            self.scheduler.add_job(
                self.post_random_ad,
                trigger=trigger,
                id=f"ad_post_{hour}_{minute}",
                replace_existing=True
            )
            logger.info(f"Scheduled ad post for {hour:02d}:{minute:02d}")
        
        # Also schedule a job to regenerate times daily at midnight
        self.scheduler.add_job(
            self._reschedule_daily_ads,
            trigger=CronTrigger(hour=0, minute=0),
            id="reschedule_ads",
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_running = True
        logger.info("✅ Ad scheduler started")
    
    def _reschedule_daily_ads(self):
        """Reschedule ads with new random times for the next day"""
        # Remove old ad jobs
        for job in self.scheduler.get_jobs():
            if job.id.startswith("ad_post_"):
                self.scheduler.remove_job(job.id)
        
        # Generate new random times
        posting_times = self._generate_random_times(DAILY_AD_COUNT)
        
        # Schedule new ads
        for hour, minute in posting_times:
            trigger = CronTrigger(hour=hour, minute=minute)
            self.scheduler.add_job(
                self.post_random_ad,
                trigger=trigger,
                id=f"ad_post_{hour}_{minute}",
                replace_existing=True
            )
            logger.info(f"Rescheduled ad post for {hour:02d}:{minute:02d}")
    
    def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            return
        
        self.scheduler.shutdown()
        self.is_running = False
        logger.info("Scheduler stopped")
    
    async def post_manual_ad(self, toy_id: int = None) -> bool:
        """
        Manually post an advertisement (admin triggered)
        
        Args:
            toy_id: Optional specific toy ID, or None for random
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if GROUP_CHAT_ID == 0:
                logger.warning("GROUP_CHAT_ID not configured")
                return False
            
            db = get_db_session()
            try:
                if toy_id:
                    toy = CatalogService.get_toy_by_id(db, toy_id)
                    if not toy or not toy.is_active:
                        return False
                    toys = [toy]
                else:
                    toys = CatalogService.get_random_active_toys_for_ad(
                        db, 
                        count=1, 
                        exclude_today=False  # Allow manual posts even if posted today
                    )
                    if not toys:
                        return False
                
                toy = toys[0]
                
                # Format advertisement message
                message_text = (
                    f"🎁 <b>{toy.title}</b>\n\n"
                    f"💰 Narxi: {toy.price}\n\n"
                    f"{toy.description}\n\n"
                    f"📦 Buyurtma berish uchun botga yozing: @{self.bot.username}"
                )
                
                # Send media with caption
                if toy.media_type == "image":
                    await self.bot.send_photo(
                        chat_id=GROUP_CHAT_ID,
                        photo=toy.media_file_id,
                        caption=message_text,
                        parse_mode="HTML"
                    )
                elif toy.media_type == "video":
                    await self.bot.send_video(
                        chat_id=GROUP_CHAT_ID,
                        video=toy.media_file_id,
                        caption=message_text,
                        parse_mode="HTML"
                    )
                
                logger.info(f"Manually posted ad for toy ID {toy.id} ({toy.title})")
                return True
                
            except Exception as e:
                logger.error(f"Error in manual ad post: {e}", exc_info=True)
                return False
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Critical error in post_manual_ad: {e}", exc_info=True)
            return False
