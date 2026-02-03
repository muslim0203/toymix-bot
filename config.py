"""
Configuration file for Yaypan Toymix Telegram Bot
Production-ready: All values from environment variables
"""
import os
import sys
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file (for local development only)
# In production, environment variables should be set by the hosting platform
load_dotenv()


def get_required_env(key: str, default: str = None) -> str:
    """
    Get required environment variable
    
    Args:
        key: Environment variable key
        default: Optional default value (for development only)
        
    Returns:
        Environment variable value
        
    Raises:
        SystemExit: If variable is not set and no default provided
    """
    value = os.getenv(key, default)
    if value is None:
        print(f"❌ ERROR: Required environment variable '{key}' is not set!")
        print(f"   Please set {key} in your environment or .env file")
        sys.exit(1)
    return value


def get_optional_env(key: str, default: str) -> str:
    """Get optional environment variable with default"""
    return os.getenv(key, default)


def get_int_env(key: str, default: int) -> int:
    """Get integer environment variable with default"""
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


def get_list_env(key: str, default: List[int] = None) -> List[int]:
    """
    Get list of integers from comma-separated environment variable
    
    Args:
        key: Environment variable key
        default: Default list if not set
        
    Returns:
        List of integers
    """
    if default is None:
        default = []
    
    env_value = os.getenv(key, "")
    if not env_value:
        return default
    
    try:
        return [
            int(admin_id.strip())
            for admin_id in env_value.split(",")
            if admin_id.strip().isdigit()
        ]
    except ValueError:
        return default


# ============================================================================
# REQUIRED CONFIGURATION (must be set in production)
# ============================================================================

# Bot Token from @BotFather
BOT_TOKEN: str = get_required_env("BOT_TOKEN")

# Admin user IDs (comma-separated in env: "123,456,789")
# Example: ADMIN_IDS=470989841,5702173054,618269854
ADMIN_IDS: List[int] = get_list_env("ADMIN_IDS", [
    470989841,
    5702173054,
    618269854,
    539783187,
    1982313851,
])

# Group chat ID where ads will be posted
# CRITICAL: Must be set in environment variable for production
# Format: -1001234567890 (negative integer for groups/supergroups)
# Set to "0" to disable group ads
GROUP_CHAT_ID_RAW = os.getenv("GROUP_CHAT_ID")
if GROUP_CHAT_ID_RAW:
    try:
        GROUP_CHAT_ID: int = int(GROUP_CHAT_ID_RAW)
        if GROUP_CHAT_ID > 0:
            print(f"⚠️  WARNING: GROUP_CHAT_ID is positive ({GROUP_CHAT_ID}). Groups usually have negative IDs (e.g., -1001234567890)")
    except ValueError:
        print(f"❌ ERROR: GROUP_CHAT_ID must be an integer, got: {GROUP_CHAT_ID_RAW}")
        GROUP_CHAT_ID: int = 0
else:
    # Default fallback (development only)
    GROUP_CHAT_ID: int = -1003835595470
    print("⚠️  WARNING: GROUP_CHAT_ID not set in environment, using default. Set GROUP_CHAT_ID env var for production.")

# Database URL
# SQLite (dev): sqlite:///toymix.db
# PostgreSQL (prod): postgresql://user:pass@host:port/dbname
# PostgreSQL async (prod): postgresql+asyncpg://user:pass@host:port/dbname
#
# PRODUCTION SAFETY: Single database engine ensures data consistency
# All services use the same SessionLocal factory from database/db.py
DATABASE_URL: str = get_optional_env("DATABASE_URL", "sqlite:///toymix.db")

# ============================================================================
# MARKETING CONFIGURATION
# ============================================================================

# Bot username (with @)
BOT_USERNAME: str = get_optional_env("BOT_USERNAME", "@YaypanToymixBot")

# Group invite link
GROUP_LINK: str = get_optional_env("GROUP_LINK", "https://t.me/yaypantoymix")

# Order phone number
ORDER_PHONE: str = get_optional_env("ORDER_PHONE", "+998901234567")

# ============================================================================
# SCHEDULER CONFIGURATION
# ============================================================================

# Number of ads per day
DAILY_AD_COUNT: int = get_int_env("DAILY_AD_COUNT", 15)

# Ad posting time window
AD_START_HOUR: int = get_int_env("AD_START_HOUR", 9)  # 09:00
AD_END_HOUR: int = get_int_env("AD_END_HOUR", 21)  # 21:00

# Interval between ads (minutes)
AD_MIN_INTERVAL: int = get_int_env("AD_MIN_INTERVAL", 30)
AD_MAX_INTERVAL: int = get_int_env("AD_MAX_INTERVAL", 90)

# ============================================================================
# APPLICATION CONFIGURATION
# ============================================================================

# Pagination
ITEMS_PER_PAGE: int = get_int_env("ITEMS_PER_PAGE", 5)

# Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL: str = get_optional_env("LOG_LEVEL", "INFO").upper()

# ============================================================================
# VALIDATION
# ============================================================================

# Validate critical settings
if not BOT_TOKEN or len(BOT_TOKEN) < 10:
    print("❌ ERROR: BOT_TOKEN is invalid!")
    sys.exit(1)

if not ADMIN_IDS:
    print("⚠️  WARNING: No admin IDs configured. Admin features will be disabled.")

if AD_START_HOUR >= AD_END_HOUR:
    print("⚠️  WARNING: AD_START_HOUR must be less than AD_END_HOUR")
    print(f"   Using defaults: 9-21")
    AD_START_HOUR = 9
    AD_END_HOUR = 21

if AD_MIN_INTERVAL >= AD_MAX_INTERVAL:
    print("⚠️  WARNING: AD_MIN_INTERVAL must be less than AD_MAX_INTERVAL")
    print(f"   Using defaults: 30-90")
    AD_MIN_INTERVAL = 30
    AD_MAX_INTERVAL = 90

# Note: Order contacts are managed via admin panel
# They are stored in the order_contacts database table
