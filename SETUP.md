# Quick Setup Guide

## 🚀 Quick Start

1. **Install Python 3.11+**
   ```bash
   python3 --version  # Should be 3.11 or higher
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your BOT_TOKEN, ADMIN_IDS, and GROUP_CHAT_ID
   ```

5. **Run the bot**
   ```bash
   python bot.py
   # Or use the run script:
   ./run.sh
   ```

## 📝 Getting Required IDs

### Bot Token
1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow instructions
3. Copy the token (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Admin User IDs
1. Send a message to [@userinfobot](https://t.me/userinfobot)
2. Copy your ID (number like: `123456789`)

### Group Chat ID
1. Add [@getidsbot](https://t.me/getidsbot) to your group
2. The bot will show the group ID (usually negative: `-1001234567890`)
3. Make sure your bot is added to the group as an admin

## ✅ Verification

After starting the bot, you should see:
- ✅ Database initialized successfully
- ✅ Ad scheduler started
- ✅ Bot started: @your_bot_name

Test the bot:
- Send `/start` to see user menu
- Send `/admin` (if you're an admin) to see admin panel

## 🐛 Troubleshooting

**Bot not starting?**
- Check `BOT_TOKEN` is correct
- Verify Python version is 3.11+

**Scheduler not working?**
- Check `GROUP_CHAT_ID` is correct
- Verify bot is admin in the group
- Check logs in `bot.log`

**Database errors?**
- Ensure write permissions in the directory
- For SQLite, the file will be created automatically
