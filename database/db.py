"""
Database connection and session management
Production-ready with async support
"""
import logging
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool, NullPool
from sqlalchemy.engine import Engine

from config import DATABASE_URL
from database.models import (
    Base, Toy, DailyAd, Category, DailyAdsLog, OrderContact, SalesLog,
    BestsellerCategory, StoreLocation, CartItem, Favorite, ToyMedia
)

logger = logging.getLogger(__name__)


# Create engine based on database URL
if DATABASE_URL.startswith("sqlite"):
    # SQLite configuration for development
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
        pool_pre_ping=True  # Verify connections before using
    )
    logger.info("Using SQLite database (development mode)")
elif DATABASE_URL.startswith("postgresql"):
    # PostgreSQL configuration for production
    # Support both sync and async URLs
    if "+asyncpg" in DATABASE_URL:
        # Async PostgreSQL - use asyncpg driver
        logger.info("Using PostgreSQL with asyncpg (async mode)")
        # For sync operations, remove asyncpg from URL
        sync_url = DATABASE_URL.replace("+asyncpg", "")
        engine = create_engine(
            sync_url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            echo=False
        )
    else:
        # Sync PostgreSQL
        logger.info("Using PostgreSQL (sync mode)")
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            echo=False
        )
else:
    # Other databases (MySQL, etc.)
    logger.info(f"Using database: {DATABASE_URL.split('://')[0]}")
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        echo=False
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Initialize database tables
    Production-ready: Creates all tables if they don't exist
    """
    try:
        logger.info("Initializing database...")
        
        # First, run migration to add category_id if needed (SQLite only)
        if DATABASE_URL.startswith("sqlite"):
            try:
                from database.migrate import migrate_database
                migrate_database()
            except Exception as e:
                logger.warning(f"Migration warning: {e}")
                logger.info("Continuing with table creation...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created/verified successfully")
        
        # Verify database connection
        db = SessionLocal()
        try:
            # Test query
            from database.models import Category
            category_count = db.query(Category).count()
            logger.info(f"Database connection verified. Categories: {category_count}")
            
            if category_count == 0:
                logger.info("No categories found. You can add categories via admin panel.")
        except Exception as e:
            logger.error(f"Database verification failed: {e}", exc_info=True)
            raise
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        logger.error("Please check your DATABASE_URL configuration")
        raise


def get_db() -> Session:
    """
    Get database session (dependency injection pattern)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """
    Get a database session (for direct use)
    """
    return SessionLocal()
