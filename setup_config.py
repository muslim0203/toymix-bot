#!/usr/bin/env python3
"""
Setup script to create .env file with bot configuration
"""
import os

def create_env_file():
    """Create .env file with configuration"""
    env_content = """# Yaypan Toymix Telegram Bot Configuration

# Bot Token from @BotFather
BOT_TOKEN=8305995072:AAGlU_0EWxG-WMRUxz7CFMhzdmV2GnVxlAM

# Admin user IDs (comma-separated)
# Get your ID from @userinfobot on Telegram
ADMIN_IDS=

# Group chat ID where ads will be posted (negative number for groups)
# Get group ID from @getidsbot on Telegram
GROUP_CHAT_ID=

# Number of ads to post per day (5-6 recommended)
DAILY_AD_COUNT=5

# Ad posting time window (24-hour format)
AD_START_HOUR=9
AD_END_HOUR=21

# Database URL
DATABASE_URL=sqlite:///toymix.db

# Logging level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
"""
    
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    
    if os.path.exists(env_path):
        response = input(f".env file already exists. Overwrite? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return
    
    try:
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print(f"✅ .env file created successfully at: {env_path}")
        print("\n⚠️  IMPORTANT: Please edit .env and add:")
        print("   1. ADMIN_IDS - Your Telegram user ID (get from @userinfobot)")
        print("   2. GROUP_CHAT_ID - Your group chat ID (get from @getidsbot)")
        print("\nAfter editing, you can run the bot with: python bot.py")
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        print("\nPlease create .env file manually with the following content:")
        print(env_content)

if __name__ == "__main__":
    create_env_file()
