"""
Configuration file for Yaypan Toymix Telegram Bot
Production-ready: All values from environment variables
"""
import os
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file (for local development only)
load_dotenv()


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
    """Get list of integers from comma-separated environment variable"""
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


# Bot Token from @BotFather
BOT_TOKEN: str = get_optional_env("BOT_TOKEN", "")

# Admin user IDs (comma-separated in env: "123,456,789")
ADMIN_IDS: List[int] = get_list_env("ADMIN_IDS", [
    470989841,
    5702173054,
    618269854,
    539783187,
    1982313851,
])

# Group chat ID where ads will be posted
# Format: -1001234567890 (negative integer for groups/supergroups)
# Set to "0" to disable group ads
GROUP_CHAT_ID: int = get_int_env("GROUP_CHAT_ID", 0)

# Database URL
DATABASE_URL: str = get_optional_env("DATABASE_URL", "sqlite:///toymix.db")

# Bot username (with @)
BOT_USERNAME: str = get_optional_env("BOT_USERNAME", "@YaypanToymixBot")

# Group invite link
GROUP_LINK: str = get_optional_env("GROUP_LINK", "https://t.me/yaypantoymix")

# Order phone number
ORDER_PHONE: str = get_optional_env("ORDER_PHONE", "+998902699198")

# Number of ads per day
DAILY_AD_COUNT: int = get_int_env("DAILY_AD_COUNT", 15)

# Ad posting time window
AD_START_HOUR: int = get_int_env("AD_START_HOUR", 9)
AD_END_HOUR: int = get_int_env("AD_END_HOUR", 21)

# Interval between ads (minutes)
AD_MIN_INTERVAL: int = get_int_env("AD_MIN_INTERVAL", 30)
AD_MAX_INTERVAL: int = get_int_env("AD_MAX_INTERVAL", 90)

# Pagination
ITEMS_PER_PAGE: int = get_int_env("ITEMS_PER_PAGE", 5)

# Logging level
LOG_LEVEL: str = get_optional_env("LOG_LEVEL", "INFO").upper()
