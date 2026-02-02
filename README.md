# Yaypan Toymix Telegram Bot

A scalable Telegram bot for managing and advertising a toy shop catalog.

## 🎯 Features

### User Features
- 📦 Browse toy catalog with pagination
- 🛒 Place orders for toys
- 📱 User-friendly interface in Uzbek language

### Admin Features
- ➕ Add new toys (with image/video)
- ✏️ Edit existing toys
- 🗑️ Delete toys
- ✅ Enable/disable toys
- 📊 View catalog statistics
- 📢 Manually trigger advertisements

### Automated Features
- 🤖 Automatic daily advertisements (5-6 per day)
- ⏰ Randomized posting times (09:00 - 21:00)
- 🔄 Prevents duplicate ads on the same day
- 📅 Scheduler automatically reschedules daily

## 🏗️ Architecture

```
toymix_bot/
├── bot.py                 # Main bot entry point
├── config.py             # Configuration settings
├── database/
│   ├── models.py         # SQLAlchemy models
│   └── db.py             # Database connection
├── handlers/
│   ├── user.py           # User command handlers
│   └── admin.py          # Admin command handlers
├── services/
│   ├── catalog_service.py # Catalog business logic
│   └── scheduler.py      # Advertisement scheduler
├── keyboards/
│   ├── user_kb.py        # User keyboard layouts
│   └── admin_kb.py       # Admin keyboard layouts
├── utils/
│   └── random_ads.py     # Utility functions
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## 📋 Prerequisites

- Python 3.11+
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Admin Telegram User IDs
- Group Chat ID (for advertisements)

## 🚀 Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd toymix_bot
   ```

2. **Create a virtual environment:**
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   
   Create a `.env` file in the `toymix_bot` directory:
   ```env
   BOT_TOKEN=your_bot_token_here
   ADMIN_IDS=123456789,987654321
   GROUP_CHAT_ID=-1001234567890
   DAILY_AD_COUNT=5
   AD_START_HOUR=9
   AD_END_HOUR=21
   DATABASE_URL=sqlite:///toymix.db
   LOG_LEVEL=INFO
   ```

   Or export them directly:
   ```bash
   export BOT_TOKEN="your_bot_token_here"
   export ADMIN_IDS="123456789,987654321"
   export GROUP_CHAT_ID="-1001234567890"
   ```

5. **Initialize the database:**
   The database will be automatically initialized on first run.

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `BOT_TOKEN` | Telegram bot token from @BotFather | ✅ Yes | - |
| `ADMIN_IDS` | Comma-separated admin user IDs | ✅ Yes | - |
| `GROUP_CHAT_ID` | Telegram group chat ID for ads | ✅ Yes | - |
| `DAILY_AD_COUNT` | Number of ads per day | No | 5 |
| `AD_START_HOUR` | Start hour for ad window | No | 9 |
| `AD_END_HOUR` | End hour for ad window | No | 21 |
| `DATABASE_URL` | Database connection string | No | `sqlite:///toymix.db` |
| `LOG_LEVEL` | Logging level | No | INFO |

### Getting Your Chat ID

1. **User ID (for ADMIN_IDS):**
   - Send a message to [@userinfobot](https://t.me/userinfobot)
   - Copy your ID

2. **Group Chat ID:**
   - Add [@getidsbot](https://t.me/getidsbot) to your group
   - Copy the group ID (usually negative number like `-1001234567890`)

## 🎮 Usage

### Starting the Bot

```bash
python bot.py
```

### User Commands

- `/start` - Start the bot and see welcome message
- Browse catalog using inline buttons
- Place orders through the interface

### Admin Commands

- `/admin` - Open admin panel
- Use inline buttons to manage toys and catalog

## 📊 Database

### Development (SQLite)
- Database file: `toymix.db`
- Automatically created on first run
- No additional setup required

### Production (PostgreSQL)
1. Install PostgreSQL
2. Create database:
   ```sql
   CREATE DATABASE toymix_bot;
   ```
3. Update `DATABASE_URL` in `.env`:
   ```env
   DATABASE_URL=postgresql://user:password@localhost/toymix_bot
   ```

## 🔐 Security

- Admin commands are protected by `ADMIN_IDS` check
- Only authorized users can manage the catalog
- Media files are stored as Telegram `file_id` (no external storage)

## 📝 Database Schema

### `toys` Table
- `id` (Integer, Primary Key)
- `title` (String)
- `price` (String)
- `description` (Text)
- `media_type` (String: 'image' or 'video')
- `media_file_id` (String: Telegram file_id)
- `is_active` (Boolean)
- `created_at` (DateTime)
- `updated_at` (DateTime)

### `daily_ads` Table
- `id` (Integer, Primary Key)
- `toy_id` (Integer, Foreign Key)
- `posted_date` (String: YYYY-MM-DD)
- `posted_at` (DateTime)

## 🚀 Deployment

### VPS Deployment

1. **Install dependencies on server:**
   ```bash
   sudo apt update
   sudo apt install python3.11 python3.11-venv
   ```

2. **Clone and set up:**
   ```bash
   git clone <your-repo>
   cd toymix_bot
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Set up systemd service:**
   
   Create `/etc/systemd/system/toymix-bot.service`:
   ```ini
   [Unit]
   Description=Yaypan Toymix Telegram Bot
   After=network.target

   [Service]
   Type=simple
   User=your-user
   WorkingDirectory=/path/to/toymix_bot
   Environment="PATH=/path/to/toymix_bot/venv/bin"
   ExecStart=/path/to/toymix_bot/venv/bin/python bot.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

4. **Start service:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable toymix-bot
   sudo systemctl start toymix-bot
   ```

### Railway / Render Deployment

1. Add environment variables in dashboard
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `python bot.py`
4. Deploy!

## 🐛 Troubleshooting

### Bot not responding
- Check `BOT_TOKEN` is correct
- Verify bot is not blocked
- Check logs in `bot.log`

### Scheduler not working
- Verify `GROUP_CHAT_ID` is correct
- Check bot is added to the group as admin
- Review scheduler logs

### Database errors
- Ensure database file has write permissions (SQLite)
- Check PostgreSQL connection (production)
- Verify `DATABASE_URL` format

## 📝 Logging

Logs are written to:
- Console (stdout)
- File: `bot.log`

Set `LOG_LEVEL` to `DEBUG` for detailed logs.

## 🔄 Updates

To update the bot:
1. Pull latest changes
2. Update dependencies: `pip install -r requirements.txt --upgrade`
3. Restart the bot

## 📄 License

This project is proprietary software for Yaypan Toymix.

## 👥 Support

For issues or questions, contact the development team.

---

**Built with ❤️ using aiogram 3.x**
