"""
Enhanced scheduler service for category-based daily advertisements
"""
import logging
import random
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import (
    DAILY_AD_COUNT, AD_START_HOUR, AD_END_HOUR, GROUP_CHAT_ID,
    AD_MIN_INTERVAL, AD_MAX_INTERVAL
)
from services.ads_selector import AdsSelector
from services.ads_formatter import AdsFormatter
from services.media_service import MediaService
from services.order_contact_service import OrderContactService
from database.db import get_db_session

logger = logging.getLogger(__name__)


class CategoryBasedAdScheduler:
    """Scheduler for category-based automated toy advertisements"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
    
    
    async def post_category_based_ad(self):
        """
        Post a random toy advertisement from a random category
        This function is called by the scheduler
        """
        try:
            if GROUP_CHAT_ID == 0:
                logger.warning("GROUP_CHAT_ID not configured, skipping ad post")
                return
            
            db = get_db_session()
            try:
                # Get random category and toy
                result = AdsSelector.get_random_category_toy_pair(db, exclude_today=True)
                
                if not result:
                    logger.info("No toys available for posting today")
                    return
                
                category, toy = result
                
                # Small delay to avoid flood control
                import asyncio
                await asyncio.sleep(1)
                
                # Check if toy has multiple media (media group)
                toy_media = MediaService.get_toy_media(db, toy.id)
                
                if toy_media and len(toy_media) > 0:
                    # Send media group
                    media_group = MediaService.get_media_for_media_group(toy_media)
                    sent_messages = await self.bot.send_media_group(
                        chat_id=GROUP_CHAT_ID,
                        media=media_group
                    )
                    
                    # Format and send advertisement message
                    message_text = AdsFormatter.format_ad_message(toy, category)
                    keyboard = AdsFormatter.get_ad_keyboard(toy.id)
                    
                    await self.bot.send_message(
                        chat_id=GROUP_CHAT_ID,
                        text=message_text,
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )
                else:
                    # Fallback to single media (backward compatibility)
                    message_text = AdsFormatter.format_ad_message(toy, category)
                    keyboard = AdsFormatter.get_ad_keyboard(toy.id)
                    
                    if toy.media_type == "image" and toy.media_file_id:
                        await self.bot.send_photo(
                            chat_id=GROUP_CHAT_ID,
                            photo=toy.media_file_id,
                            caption=message_text,
                            parse_mode="HTML",
                            reply_markup=keyboard
                        )
                    elif toy.media_type == "video" and toy.media_file_id:
                        await self.bot.send_video(
                            chat_id=GROUP_CHAT_ID,
                            video=toy.media_file_id,
                            caption=message_text,
                            parse_mode="HTML",
                            reply_markup=keyboard
                        )
                    else:
                        # No media, send text only
                        await self.bot.send_message(
                            chat_id=GROUP_CHAT_ID,
                            text=message_text,
                            parse_mode="HTML",
                            reply_markup=keyboard
                        )
                
                # Log the ad
                AdsSelector.log_ad_posted(db, toy.id, category.id if category else None)
                
                category_name = category.name if category else "Kategoriyasiz"
                logger.info(f"Posted ad for toy ID {toy.id} ({toy.title}) from category {category_name}")
                
            except Exception as e:
                logger.error(f"Error posting ad: {e}", exc_info=True)
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Critical error in post_category_based_ad: {e}", exc_info=True)
    
    def _generate_random_times(self, count: int) -> list:
        """
        Generate random times with intervals between AD_MIN_INTERVAL-AD_MAX_INTERVAL minutes
        
        Args:
            count: Number of ads to schedule
            
        Returns:
            List of (hour, minute) tuples
        """
        times = []
        current_hour = AD_START_HOUR
        current_minute = random.randint(0, 30)  # Start at random minute within first hour
        
        for _ in range(count):
            # Add random interval
            interval_minutes = random.randint(AD_MIN_INTERVAL, AD_MAX_INTERVAL)
            current_minute += interval_minutes
            
            # Handle hour overflow
            while current_minute >= 60:
                current_minute -= 60
                current_hour += 1
            
            # Check if we're still within time window
            if current_hour >= AD_END_HOUR:
                break
            
            times.append((current_hour, current_minute))
        
        return times
    
    def start(self):
        """Start the scheduler"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        # Generate random posting times
        posting_times = self._generate_random_times(DAILY_AD_COUNT)
        
        if not posting_times:
            logger.warning("No valid posting times generated")
            return
        
        # Schedule ads at random times
        for hour, minute in posting_times:
            trigger = CronTrigger(hour=hour, minute=minute)
            self.scheduler.add_job(
                self.post_category_based_ad,
                trigger=trigger,
                id=f"cat_ad_post_{hour}_{minute}",
                replace_existing=True
            )
            logger.info(f"Scheduled category-based ad post for {hour:02d}:{minute:02d}")
        
        # Schedule daily rescheduling at midnight
        self.scheduler.add_job(
            self._reschedule_daily_ads,
            trigger=CronTrigger(hour=0, minute=0),
            id="reschedule_cat_ads",
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_running = True
        logger.info("✅ Category-based ad scheduler started")
    
    def _reschedule_daily_ads(self):
        """Reschedule ads with new random times for the next day"""
        # Remove old ad jobs
        for job in self.scheduler.get_jobs():
            if job.id.startswith("cat_ad_post_"):
                self.scheduler.remove_job(job.id)
        
        # Generate new random times
        posting_times = self._generate_random_times(DAILY_AD_COUNT)
        
        if not posting_times:
            logger.warning("No valid posting times generated for reschedule")
            return
        
        # Schedule new ads
        for hour, minute in posting_times:
            trigger = CronTrigger(hour=hour, minute=minute)
            self.scheduler.add_job(
                self.post_category_based_ad,
                trigger=trigger,
                id=f"cat_ad_post_{hour}_{minute}",
                replace_existing=True
            )
            logger.info(f"Rescheduled category-based ad post for {hour:02d}:{minute:02d}")
    
    def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            return
        
        self.scheduler.shutdown()
        self.is_running = False
        logger.info("Category-based scheduler stopped")
    
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
                    from services.catalog_service import CatalogService
                    toy = CatalogService.get_toy_by_id(db, toy_id)
                    if not toy or not toy.is_active:
                        return False
                    
                    category = toy.category if toy.category else None
                    category_name = category.name if category else "Kategoriyasiz"
                else:
                    result = AdsSelector.get_random_category_toy_pair(db, exclude_today=False)
                    if not result:
                        return False
                    category, toy = result
                    category_name = category.name
                
                # Check if toy has multiple media (media group)
                toy_media = MediaService.get_toy_media(db, toy.id)
                
                if toy_media and len(toy_media) > 0:
                    # Send media group
                    media_group = MediaService.get_media_for_media_group(toy_media)
                    sent_messages = await self.bot.send_media_group(
                        chat_id=GROUP_CHAT_ID,
                        media=media_group
                    )
                    
                    # Format and send advertisement message
                    category_obj = category if category else None
                    message_text = AdsFormatter.format_ad_message(toy, category_obj)
                    keyboard = AdsFormatter.get_ad_keyboard(toy.id)
                    
                    await self.bot.send_message(
                        chat_id=GROUP_CHAT_ID,
                        text=message_text,
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )
                else:
                    # Fallback to single media
                    category_obj = category if category else None
                    message_text = AdsFormatter.format_ad_message(toy, category_obj)
                    keyboard = AdsFormatter.get_ad_keyboard(toy.id)
                    
                    if toy.media_type == "image" and toy.media_file_id:
                        await self.bot.send_photo(
                            chat_id=GROUP_CHAT_ID,
                            photo=toy.media_file_id,
                            caption=message_text,
                            parse_mode="HTML",
                            reply_markup=keyboard
                        )
                    elif toy.media_type == "video" and toy.media_file_id:
                        await self.bot.send_video(
                            chat_id=GROUP_CHAT_ID,
                            video=toy.media_file_id,
                            caption=message_text,
                            parse_mode="HTML",
                            reply_markup=keyboard
                        )
                    else:
                        # No media, send text only
                        await self.bot.send_message(
                            chat_id=GROUP_CHAT_ID,
                            text=message_text,
                            parse_mode="HTML",
                            reply_markup=keyboard
                        )
                
                # Log if not manual specific toy
                if not toy_id:
                    AdsSelector.log_ad_posted(db, toy.id, toy.category_id if toy.category else None)
                
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
