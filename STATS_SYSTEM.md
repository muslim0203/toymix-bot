# Sotuv Statistikasi Tizimi

## ✅ Qo'shilgan Funksiyalar

### PART 1 - Sotuv Tracking

1. **Avtomatik Logging**
   - Har safar foydalanuvchi "🛒 Buyurtma berish" tugmasini bosganda log yoziladi
   - Katalogdan buyurtma berish
   - Reklamadan buyurtma berish
   - Barcha buyurtmalar `sales_logs` jadvalida saqlanadi

2. **Ma'lumotlar**
   - `user_id` - Foydalanuvchi ID
   - `toy_id` - O'yinchoq ID
   - `toy_name` - O'yinchoq nomi (denormalized)
   - `category_id` - Kategoriya ID
   - `category_name` - Kategoriya nomi (denormalized)
   - `created_at` - Vaqt (indexed)

### PART 2 - Statistika Oqimlari

1. **Admin Panel**
   - "📊 Sotuv statistikasi" tugmasi
   - Kategoriya bo'yicha statistika
   - O'yinchoq bo'yicha statistika

2. **Davr Tanlash**
   - 📅 Haftalik (oxirgi 7 kun)
   - 📅 Oylik (joriy oy)
   - 📅 Yillik (joriy yil)

3. **Statistika Formatlari**
   - Kategoriya bo'yicha: Top kategoriyalar ro'yxati
   - O'yinchoq bo'yicha: Top o'yinchoqlar ro'yxati
   - Har birida sonlar ko'rsatiladi

## 📊 Statistika Misollari

### Kategoriya Bo'yicha (Oylik)
```
📊 Oylik sotuv statistikasi (kategoriya bo'yicha):

1️⃣ 🧸 Yumshoq o'yinchoqlar — 42 ta
2️⃣ 🚗 Mashinalar — 31 ta
3️⃣ 🧠 Rivojlantiruvchi — 18 ta
```

### O'yinchoq Bo'yicha (Haftalik)
```
📊 Haftalik sotuv statistikasi (o'yinchoq bo'yicha):

1️⃣ Teddy Bear XL — 15 ta
2️⃣ Hot Wheels Track — 11 ta
3️⃣ Lego Classic — 7 ta
```

## 🗂 Database Strukturasi

### sales_logs Jadvali
- `id` - Primary key
- `user_id` - Foydalanuvchi ID (indexed)
- `toy_id` - O'yinchoq ID (indexed, FK)
- `toy_name` - O'yinchoq nomi (denormalized)
- `category_id` - Kategoriya ID (indexed, FK)
- `category_name` - Kategoriya nomi (denormalized)
- `created_at` - Vaqt (indexed)

## 🔍 SQL Queries

### Kategoriya Bo'yicha (Haftalik)
```sql
SELECT category_name, COUNT(*) as count
FROM sales_logs
WHERE created_at >= DATE('now', '-7 days')
  AND category_name IS NOT NULL
GROUP BY category_name
ORDER BY count DESC
```

### O'yinchoq Bo'yicha (Oylik)
```sql
SELECT toy_name, COUNT(*) as count
FROM sales_logs
WHERE strftime('%Y', created_at) = strftime('%Y', 'now')
  AND strftime('%m', created_at) = strftime('%m', 'now')
GROUP BY toy_name
ORDER BY count DESC
```

## 🚀 Ishlatish

### Admin Panel
1. `/admin` → `📊 Sotuv statistikasi`
2. `📂 Kategoriya bo'yicha` yoki `🧸 O'yinchoq bo'yicha`
3. `📅 Haftalik` / `📅 Oylik` / `📅 Yillik`
4. Statistika ko'rsatiladi

### Avtomatik Tracking
- Foydalanuvchi "🛒 Buyurtma berish" tugmasini bosganda
- Avtomatik log yoziladi
- Hech qanday qo'shimcha harakat kerak emas

## 📝 Eslatmalar

1. **Denormalized Data**: Tezroq analytics uchun nomlar saqlanadi
2. **Indexes**: Performance uchun barcha kerakli ustunlar indexed
3. **SQL GROUP BY**: Memory'da emas, SQL'da aggregation
4. **Empty Stats**: Agar ma'lumot bo'lmasa, aniq xabar ko'rsatiladi

## ✅ Test Qilish

1. Botni ishga tushiring
2. Bir nechta buyurtma berishni simulyatsiya qiling
3. Admin panel → Sotuv statistikasi → Kategoriya/O'yinchoq → Davr
4. Statistika ko'rsatilishi kerak
