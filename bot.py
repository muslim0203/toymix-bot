"""
Main bot file for Yaypan Toymix Telegram Bot
Production-ready entry point with graceful shutdown
"""
import asyncio
import logging
import sys
import signal
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.exceptions import TelegramNetworkError, TelegramAPIError

from config import BOT_TOKEN, LOG_LEVEL, GROUP_CHAT_ID
from database.db import init_db
from handlers import (
    user, admin, admin_category_manage, admin_contacts, admin_stats,
    admin_bestseller, user_bestseller, user_locations, user_about, admin_locations,
    user_cart, user_favorites, user_navigation
)
from services.ads_scheduler import CategoryBasedAdScheduler
from services.bestseller_scheduler import BestsellerScheduler

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

# Global variables for graceful shutdown
bot_instance = None
scheduler_instance = None
bestseller_scheduler_instance = None
dispatcher_instance = None


def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        if bot_instance:
            asyncio.create_task(shutdown())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def shutdown():
    """Graceful shutdown procedure"""
    logger.info("Shutting down bot...")
    
    # Stop schedulers
    if scheduler_instance:
        try:
            scheduler_instance.stop()
            logger.info("Advertisement scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
    
    if bestseller_scheduler_instance:
        try:
            bestseller_scheduler_instance.stop()
            logger.info("Bestseller scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping bestseller scheduler: {e}")
    
    # Close bot session
    if bot_instance:
        try:
            await bot_instance.session.close()
            logger.info("Bot session closed")
        except Exception as e:
            logger.error(f"Error closing bot session: {e}")
    
    logger.info("Shutdown complete")


async def main():
    """Main function to start the bot"""
    global bot_instance, scheduler_instance, bestseller_scheduler_instance, dispatcher_instance
    
    try:
        # Validate bot token
        if not BOT_TOKEN:
            logger.error("BOT_TOKEN not found in environment variables!")
            sys.exit(1)
        
        # Initialize database
        logger.info("Initializing database...")
        try:
            init_db()
        except Exception as e:
            logger.error(f"Database initialization failed: {e}", exc_info=True)
            logger.error("Bot cannot start without database. Exiting...")
            sys.exit(1)
        
        # Initialize bot and dispatcher
        logger.info("Initializing bot...")
        bot_instance = Bot(
            token=BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        dispatcher_instance = Dispatcher(storage=MemoryStorage())

        # 🔴 🔴 🔴 TEST UCHUN SHU YERGA QO'SHING 🔴 🔴 🔴
        # CRITICAL: Test message MUST go to GROUP_CHAT_ID, not private chat
        try:
            if GROUP_CHAT_ID == 0:
                logger.warning("⚠️  GROUP_CHAT_ID is 0, skipping test message")
            elif GROUP_CHAT_ID > 0:
                logger.error(f"❌ GROUP_CHAT_ID is positive ({GROUP_CHAT_ID}). Groups must have negative IDs.")
            else:
                await bot_instance.send_message(
                    chat_id=GROUP_CHAT_ID,  # CRITICAL: Must be GROUP_CHAT_ID, never message.chat.id
                    text="✅ TEST: bot guruhga xabar yubora oldi"
                )
                logger.info(f"✅ Test message sent to group {GROUP_CHAT_ID} successfully.")
        except Exception as e:
            logger.error(f"Failed to send test message to group: {e}", exc_info=True)

        # ⬇️ SHUNDAN KEYINgina qolgan kodlar
        # handlers register
        # scheduler start
        # bestseller scheduler start

        await dispatcher_instance.start_polling(bot_instance)

    except Exception as e:
        logger.critical(f"Fatal error in main(): {e}", exc_info=True)
        sys.exit(1)

        
        # Register routers (admin first to handle admin-specific buttons)
        logger.info("Registering routers...")
        dispatcher_instance.include_router(admin.router)
        dispatcher_instance.include_router(admin_category_manage.router)
        dispatcher_instance.include_router(admin_contacts.router)
        dispatcher_instance.include_router(admin_stats.router)
        dispatcher_instance.include_router(admin_bestseller.router)
        dispatcher_instance.include_router(admin_locations.router)
        dispatcher_instance.include_router(user.router)
        dispatcher_instance.include_router(user_bestseller.router)
        dispatcher_instance.include_router(user_locations.router)
        dispatcher_instance.include_router(user_about.router)
        dispatcher_instance.include_router(user_cart.router)
        dispatcher_instance.include_router(user_favorites.router)
        dispatcher_instance.include_router(user_navigation.router)
        
        # Initialize and start category-based scheduler
        logger.info("Starting category-based advertisement scheduler...")
        try:
            scheduler_instance = CategoryBasedAdScheduler(bot_instance)
            scheduler_instance.start()
            logger.info("✅ Advertisement scheduler started")
        except Exception as e:
            logger.error(f"Failed to start advertisement scheduler: {e}", exc_info=True)
            logger.warning("Continuing without advertisement scheduler...")
        
        # Initialize and start bestseller scheduler
        logger.info("Starting bestseller scheduler...")
        try:
            bestseller_scheduler_instance = BestsellerScheduler()
            bestseller_scheduler_instance.start()
            logger.info("✅ Bestseller scheduler started")
        except Exception as e:
            logger.error(f"Failed to start bestseller scheduler: {e}", exc_info=True)
            logger.warning("Continuing without bestseller scheduler...")
        
        # Get bot info
        try:
            bot_info = await bot_instance.get_me()
            logger.info(f"✅ Bot started: @{bot_info.username} ({bot_info.first_name})")
            logger.info(f"   Bot ID: {bot_info.id}")
        except TelegramNetworkError as e:
            logger.error(f"Network error connecting to Telegram: {e}")
            logger.error("Please check your internet connection and BOT_TOKEN")
            sys.exit(1)
        except TelegramAPIError as e:
            logger.error(f"Telegram API error: {e}")
            logger.error("Please check your BOT_TOKEN is valid")
            sys.exit(1)
        
        # Setup signal handlers
        setup_signal_handlers()
        
        # Start polling
        logger.info("Starting long polling...")
        await dispatcher_instance.start_polling(
            bot_instance,
            allowed_updates=dispatcher_instance.resolve_used_update_types()
        )
        
    except KeyboardInterrupt:
        logger.info("Bot interrupted by user")
    except TelegramNetworkError as e:
        logger.error(f"Telegram network error: {e}", exc_info=True)
        logger.error("This might be a temporary issue. Bot will exit.")
    except TelegramAPIError as e:
        logger.error(f"Telegram API error: {e}", exc_info=True)
        logger.error("Please check your bot configuration.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
    finally:
        await shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
