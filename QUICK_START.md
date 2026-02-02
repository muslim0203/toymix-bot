# 🚀 Tez Boshlash

## ✅ Bot Token qo'shildi!

Bot token allaqachon `config.py` fayliga qo'shildi:
- ✅ Token: `8305995072:AAGlU_0EWxG-WMRUxz7CFMhzdmV2GnVxlAM`
- ✅ Bot: @Yaypan_ToyMix

## 📝 Qolgan 2 ta sozlash

### 1️⃣ Admin ID ni topish va qo'shish

1. Telegram'da [@userinfobot](https://t.me/userinfobot) ga yozing
2. O'z ID ingizni ko'ring (masalan: `123456789`)
3. `config.py` faylini oching
4. 20-qatorda `ADMIN_IDS` ro'yxatiga ID ni qo'shing:

```python
ADMIN_IDS: List[int] = [
    123456789,  # <-- Bu yerga o'z ID ingizni yozing
]
```

### 2️⃣ Group Chat ID ni topish va qo'shish

1. Botni guruhga qo'shing va **admin** qiling
2. [@getidsbot](https://t.me/getidsbot) ni guruhga qo'shing
3. Group ID ni ko'ring (odatda manfiy: `-1001234567890`)
4. `config.py` faylini oching
5. 35-qatorda `GROUP_CHAT_ID` ni o'zgartiring:

```python
GROUP_CHAT_ID = -1001234567890  # <-- Bu yerga guruh ID ni yozing
```

## 🎯 Botni ishga tushirish

Sozlamalarni to'ldirgandan so'ng:

```bash
cd toymix_bot

# Virtual environment yaratish (bir marta)
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Kutubxonalarni o'rnatish (bir marta)
pip install -r requirements.txt

# Botni ishga tushirish
python bot.py
```

## ✅ Tekshirish

Bot ishga tushganda quyidagilarni ko'rasiz:
- ✅ Database initialized successfully
- ✅ Ad scheduler started
- ✅ Bot started: @Yaypan_ToyMix

Keyin test qiling:
- `/start` - foydalanuvchi menyusini ko'rish
- `/admin` - admin panel (agar admin bo'lsangiz)

## 🆘 Muammo bo'lsa

- Bot ishlamasa: `BOT_TOKEN` ni tekshiring
- Scheduler ishlamasa: `GROUP_CHAT_ID` ni tekshiring va bot guruhda admin ekanligini tekshiring
- Loglarni ko'rish: `bot.log` faylini oching
