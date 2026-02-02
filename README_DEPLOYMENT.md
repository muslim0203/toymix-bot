# Yaypan Toymix Bot - Production Deployment Guide

## 🚀 Quick Start

### 1. Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

**Required variables:**
- `BOT_TOKEN` - From @BotFather
- `ADMIN_IDS` - Comma-separated user IDs
- `GROUP_CHAT_ID` - Telegram group ID (or 0 to disable)
- `DATABASE_URL` - Database connection string

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Bot

```bash
python bot.py
```

## 📦 Production Deployment

### Database Setup

#### SQLite (Development)
```env
DATABASE_URL=sqlite:///toymix.db
```

#### PostgreSQL (Production - Recommended)
```env
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname
```

**Note:** For PostgreSQL, ensure `asyncpg` is installed:
```bash
pip install asyncpg
```

### Environment Variables in Production

Set all environment variables in your hosting platform:

**Railway:**
- Go to Variables tab
- Add all required variables from `.env.example`

**Heroku:**
```bash
heroku config:set BOT_TOKEN=your_token
heroku config:set ADMIN_IDS=123,456
# ... etc
```

**Docker:**
```dockerfile
ENV BOT_TOKEN=your_token
ENV ADMIN_IDS=123,456
# ... etc
```

## 🔧 Configuration

### Scheduler Settings

- `DAILY_AD_COUNT=15` - Number of ads per day
- `AD_START_HOUR=9` - Start time (24-hour format)
- `AD_END_HOUR=21` - End time (24-hour format)
- `AD_MIN_INTERVAL=30` - Minimum minutes between ads
- `AD_MAX_INTERVAL=90` - Maximum minutes between ads

### Logging

Set `LOG_LEVEL` to control verbosity:
- `DEBUG` - Detailed logs
- `INFO` - Normal operation (default)
- `WARNING` - Warnings only
- `ERROR` - Errors only

## 🛡️ Safety Features

- ✅ Graceful shutdown on SIGTERM/SIGINT
- ✅ Database connection pooling
- ✅ Error handling for Telegram API
- ✅ Scheduler prevents duplicate starts
- ✅ Auto-creates database tables
- ✅ Validates configuration on startup

## 📝 Logs

Logs are written to:
- Console (stdout)
- File: `bot.log`

In production, logs are typically captured by the hosting platform.

## ⚠️ Troubleshooting

### Bot doesn't start
1. Check `BOT_TOKEN` is valid
2. Verify database connection
3. Check logs for errors

### Scheduler not working
1. Verify `GROUP_CHAT_ID` is set correctly
2. Check bot has permission to post in group
3. Review scheduler logs

### Database errors
1. Verify `DATABASE_URL` format
2. Check database credentials
3. Ensure database exists (for PostgreSQL)

## 🔐 Security Notes

- Never commit `.env` file
- Use strong database passwords
- Rotate `BOT_TOKEN` if compromised
- Limit `ADMIN_IDS` to trusted users

## 📚 Additional Resources

- [aiogram 3.x Documentation](https://docs.aiogram.dev/)
- [APScheduler Documentation](https://apscheduler.readthedocs.io/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
