# Yangi Funksiyalar - Qo'shilgan

## ✅ PART 1 - Kategoriya Asosida Kunlik Random Reklama

### 🎯 Funksiyalar

1. **Kategoriya Asosida Reklama Tanlash**
   - Har bir reklama uchun random kategoriya tanlanadi
   - O'sha kategoriyadan random o'yinchoq tanlanadi
   - Bir kunda bir o'yinchoq ikki marta yuborilmaydi

2. **Avtomatik Rejalashtirish**
   - Har kuni 5-6 ta reklama (sozlash mumkin)
   - 09:00 - 21:00 oralig'ida
   - Reklamalar orasida 30-120 daqiqa interval
   - Har kuni 00:00 da yangi vaqtlar generatsiya qilinadi

3. **Reklama Formati (Uzbek)**
   ```
   🧸 Kategoriya: <Kategoriya nomi>
   
   📦 <O'yinchoq nomi>
   💰 Narxi: <price> so'm
   
   📝 <description>
   
   🛒 Buyurtma berish uchun tugmani bosing 👇
   ```

4. **Database Logging**
   - `daily_ads_log` jadvalida barcha reklamalar log qilinadi
   - Kategoriya va o'yinchoq ID saqlanadi
   - Dublikatlarni oldini olish uchun ishlatiladi

### 📁 Yaratilgan Fayllar

- `services/ads_selector.py` - Kategoriya asosida reklama tanlash
- `services/ads_scheduler.py` - Yangi scheduler (kategoriya asosida)
- `database/models.py` - `DailyAdsLog` modeli qo'shildi

## ✅ PART 2 - Admin Boshqariladigan Buyurtma Kontaktlari

### 🎯 Funksiyalar

1. **Kontakt Qo'shish**
   - Admin panel → "📞 Buyurtma kontaktlari" → "➕ Kontakt qo'shish"
   - Telefon raqam yoki @username qo'shish mumkin
   - Dublikatlar tekshiriladi

2. **Kontakt O'chirish**
   - Admin panel → "📞 Buyurtma kontaktlari" → "🗑 Kontakt o'chirish"
   - Soft delete (is_active = False)
   - Kontaktlar ro'yxatidan tanlash

3. **Kontaktlar Ro'yxati**
   - Admin panel → "📞 Buyurtma kontaktlari" → "📋 Kontaktlar ro'yxati"
   - Barcha faol kontaktlar ko'rsatiladi

4. **Foydalanuvchi Tomonida**
   - "🛒 Buyurtma berish" tugmasi bosilganda
   - Database'dan faol kontaktlar olinadi
   - Formatlangan ko'rinishda ko'rsatiladi

### 📁 Yaratilgan Fayllar

- `services/order_contact_service.py` - Kontaktlar boshqaruvi
- `handlers/admin_contacts.py` - Admin handlerlar
- `database/models.py` - `OrderContact` modeli qo'shildi

## 🔄 O'zgarishlar

### Database
- `daily_ads_log` jadvali qo'shildi
- `order_contacts` jadvali qo'shildi

### Bot.py
- Eski `AdScheduler` → `CategoryBasedAdScheduler` ga o'zgartirildi
- `admin_contacts` router qo'shildi

### Config.py
- `ORDER_CONTACTS` olib tashlandi (endi database'dan olinadi)

## 🚀 Ishlatish

### Reklama Tizimi
Bot avtomatik ishlaydi. Hech qanday qo'shimcha sozlash kerak emas.

### Kontaktlar Boshqaruvi
1. `/admin` → `📞 Buyurtma kontaktlari`
2. `➕ Kontakt qo'shish` - Yangi kontakt qo'shish
3. `🗑 Kontakt o'chirish` - Kontakt o'chirish
4. `📋 Kontaktlar ro'yxati` - Barcha kontaktlarni ko'rish

## 📝 Eslatmalar

1. **Reklamalar**: Bot ishga tushganda avtomatik boshlanadi
2. **Kontaktlar**: Avval admin panel orqali kontaktlar qo'shilishi kerak
3. **Database**: Yangi jadvallar avtomatik yaratiladi (migration)

## ✅ Test Qilish

1. Botni qayta ishga tushiring
2. Admin panel → Kontaktlar qo'shing
3. Reklamalar avtomatik yuboriladi (guruhda ko'rasiz)
4. Foydalanuvchi → "🛒 Buyurtma berish" → Kontaktlar ko'rsatiladi
