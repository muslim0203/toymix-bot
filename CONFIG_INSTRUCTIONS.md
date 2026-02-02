# Sozlash Ko'rsatmalari

## ✅ Bot Token qo'shildi

Bot token allaqachon `config.py` fayliga qo'shildi:
- Token: `8305995072:AAGlU_0EWxG-WMRUxz7CFMhzdmV2GnVxlAM`
- Bot: @Yaypan_ToyMix

## 📝 Qolgan sozlamalar

Quyidagilarni sozlashingiz kerak:

### 1. Admin ID ni topish
1. Telegram'da [@userinfobot](https://t.me/userinfobot) ga yozing
2. O'z ID ingizni ko'ring (masalan: `123456789`)
3. `config.py` faylida `ADMIN_IDS` ga qo'shing

### 2. Group Chat ID ni topish
1. Botni guruhga qo'shing va admin qiling
2. [@getidsbot](https://t.me/getidsbot) ni guruhga qo'shing
3. Group ID ni ko'ring (odatda manfiy raqam: `-1001234567890`)
4. `config.py` faylida `GROUP_CHAT_ID` ga qo'shing

## 🔧 Tez sozlash

`config.py` faylini ochib, quyidagilarni to'ldiring:

```python
# Admin user IDs (comma-separated in env, or list here)
ADMIN_IDS: List[int] = [
    123456789,  # <-- O'z ID ingizni qo'shing
    # Boshqa adminlar bo'lsa, vergul bilan ajrating
]

# Group chat ID where ads will be posted
GROUP_CHAT_ID: int = -1001234567890  # <-- Guruh ID ni qo'shing
```

Yoki `.env` fayl yaratib, quyidagilarni yozing:

```env
BOT_TOKEN=8305995072:AAGlU_0EWxG-WMRUxz7CFMhzdmV2GnVxlAM
ADMIN_IDS=123456789
GROUP_CHAT_ID=-1001234567890
```

## 🚀 Botni ishga tushirish

Sozlamalarni to'ldirgandan so'ng:

```bash
cd toymix_bot
python3 bot.py
```

Yoki virtual environment bilan:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python bot.py
```
