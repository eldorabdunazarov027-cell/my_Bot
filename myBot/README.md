# 🤖 Shaxsiy Vazifalar Eslatuvchi Telegram Bot

Ushbu loyiha Python, **Aiogram 3**, **APScheduler**, va **aiosqlite (SQLite)** texnologiyalari asosida yaratilgan, to‘liq o‘zbek tilida ishlaydigan zamonaviy, xavfsiz va aqlli shaxsiy yordamchi Telegram botidir.

---

## 🌟 Loyiha Imkoniyatlari

1. **👑 Maxsus Admin Tizimi:**
   - Istalgan foydalanuvchi botga kirganda umumiy qutlov oladi.
   - Botga **"Men adminman"** deb yozilganda, bot tasdiqlash uchun parol so‘raydi.
   - Boshlang‘ich admin paroli: `Parol_2012`.
   - Noto‘g‘ri parol kiritilganda: `"❌ Parol noto‘g‘ri! Qayta urinib ko‘ring."`
   - Parol xavfsizligi: Telegram xabarlarida ochiq ko‘rinmasligi uchun kiritilgan parol xabarlari bot tomonidan **darhol chatdan o‘chirib tashlanadi**.
   - **Brute-Force (buzib kirish)ga qarshi himoya:** 5 marta ketma-ket noto‘g‘ri parol kiritilsa, tizim ushbu foydalanuvchini 5 daqiqaga bloklaydi.
   - Admin parolini istalgan vaqtda admin panel orqali xavfsiz o‘zgartirish mumkin.

2. **📱 Qulay va To‘liq Admin Panel (Reply Keyboard):**
   - `➕ Vazifa qo‘shish` — Bosqichma-bosqich qulay FSM orqali yangi vazifa qo‘shish.
   - `📋 Barcha vazifalar` — Barcha faol vazifalarni ko‘rish va inline boshqarish.
   - `📅 Bugungi vazifalar` — Aynan bugungi kun uchun belgilangan vazifalar ro‘yxati.
   - `📊 Bajarilgan vazifalar` — Bajarilgan vazifalar tarixi va batafsil statistika.
   - `✏️ Vazifani tahrirlash` — Nomi, sanasi, vaqti va takrorlanishini o‘zgartirish.
   - `🗑 Vazifani o‘chirish` — Vazifani tasdiqlash orqali o‘chirish.
   - `⏰ Eslatma vaqtini belgilash` — Eslatma vaqtini tezkor o‘zgartirish.
   - `⚙️ Sozlamalar` — Bot holati, real-time Toshkent vaqti va xavfsizlik parametrlari.
   - `🔐 Parolni o‘zgartirish` — Admin parolini xavfsiz almashtirish.
   - `🚪 Admin paneldan chiqish` — Sessiyani yopish va admin paneldan chiqish.

3. **⏰ Aqlli Eslatmalar Tizimi (APScheduler):**
   - O‘zbekiston vaqti (`Asia/Tashkent`) bo‘yicha aniq soniyalarigacha ishlaydi.
   - Belgilangan vaqtda bot avtomatik quyidagi ko‘rinishda eslatma yuboradi:
     ```text
     ⏰ ESLATMA!

     📌 Vazifa: Ingliz tilini o‘rganish
     🕒 Vaqt: 18:00

     Vazifani bajarishni unutmang!
     ```
   - Xabar ostida 3 ta interaktiv tugma:
     - `✅ Bajarildi` — Vazifani bajarilgan deb belgilaydi. Agar vazifa takrorlanuvchi bo‘lsa, avtomatik ertangi kun uchun ham rejalashtiriladi!
     - `⏳ Keyinroq eslat` — Eslatmani 10 daqiqa, 30 daqiqa, 1 soat yoki 2 soatga kechiktirish (Snooze).
     - `❌ O‘tkazib yuborish` — Eslatmani bugun uchun o‘tkazib yuborish.

4. **🔄 Takrorlanuvchi Vazifalar (Har kuni):**
   - Har kuni takrorlanuvchi vazifalar bajarilganda yoki kuni o‘tganda avtomatik ravishda keyingi kunga o‘tkaziladi.

5. **💾 Doimiy Ma'lumotlar Bazasi (SQLite):**
   - SQLite ma'lumotlar bazasida vazifa nomi, sanasi, vaqti, takrorlanish holati, bajarilganligi va eslatma holati saqlanadi.
   - **Bot qayta ishga tushganda yoki server o‘chib yonganda ham barcha vazifalar saqlanib qoladi** va rejalashtirilgan eslatmalar avtomatik xotiraga qayta tiklanadi.

---

## 📁 Loyiha Tuzilmasi

```
myBot/
├── .env                  # Maxfiy sozlamalar (Bot Token, Parol, Vaqt mintaqasi)
├── .env.example          # Namuna sozlamalar fayli
├── requirements.txt      # Kutubxonalar ro'yxati
├── main.py               # Botni ishga tushiruvchi asosiy fayl
├── config.py             # Loyiha konfiguratsiyasi va o'zgaruvchilari
│
├── database/
│   ├── __init__.py
│   └── db.py             # SQLite bilan asinxron (aiosqlite) ishlash
│
├── keyboards/
│   ├── __init__.py
│   ├── reply.py          # Admin paneli va boshqa menyu klaviaturalari
│   └── inline.py         # Eslatmalar, kechiktirish va tahrirlash inline tugmalari
│
├── states/
│   ├── __init__.py
│   └── states.py         # Aiogram FSM (ketma-ket qadamlar) holatlari
│
├── services/
│   ├── __init__.py
│   ├── scheduler.py      # APScheduler: eslatmalarni rejalashtirish va qayta tiklash
│   └── security.py       # Admin autentifikatsiyasi, brute-force himoyasi
│
├── handlers/
│   ├── __init__.py
│   ├── start.py          # /start va bekor qilish xabarlari
│   ├── admin_auth.py     # "Men adminman" va parol tekshiruvi, chiqish
│   ├── task_add.py       # "➕ Vazifa qo‘shish" (nomi, sanasi, vaqti, takrorlanishi)
│   ├── task_list.py      # "📋 Barcha vazifalar", "📅 Bugungi vazifalar", "📊 Bajarilgan vazifalar"
│   ├── task_edit.py      # "✏️ Vazifani tahrirlash", "⏰ Eslatma vaqtini belgilash"
│   ├── task_delete.py    # "🗑 Vazifani o‘chirish"
│   ├── reminder_actions.py # Eslatmadagi ✅ Bajarildi, ⏳ Keyinroq eslat, ❌ O‘tkazib yuborish
│   └── settings.py       # "⚙️ Sozlamalar" va "🔐 Parolni o‘zgartirish"
│
├── tests/
│   ├── test_all.py       # Barcha bazaviy funksiyalar va xavfsizlik testlari
│   ├── test_scheduler.py # APScheduler eslatma yuborish testlari
│   └── clean_db.py       # Bazani tozalash skripti
└── README.md             # Qo'llanma va yo'riqnoma
```

---

## 🚀 O‘rnatish va Ishga Tushirish Yo‘riqnomasi

### 1-qadam: Telegram bot yaratish va token olish
1. Telegramda [@BotFather](https://t.me/BotFather) botiga kiring.
2. `/newbot` buyrug‘ini yuboring.
3. Botingizga nom va username bering.
4. BotFather sizga bergan `HTTP API Token` (masalan: `7123456789:AAH...`) ni nusxalab oling.

### 2-qadam: Sozlamalar faylini to‘ldirish
Loyiha papkasidagi `.env` faylini oching va bot tokeningizni kiriting:

```env
BOT_TOKEN=7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxx
ADMIN_PASSWORD=Parol_2012
TIMEZONE=Asia/Tashkent
MAX_FAILED_ATTEMPTS=5
LOCKOUT_MINUTES=5
```

### 3-qadam: Virtual muhit va kutubxonalarni o‘rnatish

#### Windows tizimida:
```powershell
# Virtual muhit yaratish
python -m venv .venv

# Virtual muhitni faollashtirish
.\.venv\Scripts\activate

# Kutubxonalarni o'rnatish
pip install -r requirements.txt
```

#### Linux (Ubuntu/Debian) yoki macOS tizimida:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4-qadam: Botni ishga tushirish

```bash
python main.py
```

Konsolda quyidagi xabarni ko‘rasiz:
```text
[INFO] TaskReminderBot: Ma'lumotlar bazasi (SQLite) tayyorlanmoqda...
[INFO] TaskReminderBot: APScheduler eslatmalar xizmati ishga tushdi.
[INFO] TaskReminderBot: 🤖 Bot 24/7 rejimida xabarlarni qabul qilishga tayyor!
```

---

## 🖥 Serverga (VPS / Linux Ubuntu) Joylashtirish (24/7 rejim)

Bot serverda doimiy (24/7), server qayta yoqilganda ham avtomatik ishlab turishi uchun `systemd` xizmatidan foydalanish tavsiya etiladi.

### 1. Serverga fayllarni yuklash
Serveringizga ulaning:
```bash
ssh user@your-server-ip
```
Loyihani serverga joylashtiring (masalan, `/home/ubuntu/myBot` papkasiga).

### 2. Linuxda Python va muhitni tayyorlash
```bash
sudo apt update && sudo apt install -y python3 python3-venv python3-pip
cd /home/ubuntu/myBot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Systemd servisi yaratish
Quyidagi buyruq bilan servis faylini oching:
```bash
sudo nano /etc/systemd/system/reminderbot.service
```

Quyidagi konfiguratsiyani kiriting:
```ini
[Unit]
Description=Shaxsiy Vazifalar Eslatuvchi Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/myBot
ExecStart=/home/ubuntu/myBot/.venv/bin/python /home/ubuntu/myBot/main.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

### 4. Servisni yoqish va ishga tushirish
```bash
# Systemd konfiguratsiyasini yangilash
sudo systemctl daemon-reload

# Botni avtomatik yoqilishini sozlash
sudo systemctl enable reminderbot

# Botni ishga tushirish
sudo systemctl start reminderbot

# Bot holatini tekshirish
sudo systemctl status reminderbot
```

### 5. Bot loglarini real-vaqtda kuzatish:
```bash
sudo journalctl -u reminderbot -f
```

---

## 🧪 Avtomatlashtirilgan Testlar

Loyiha to‘liq test qilingan. Barcha funksiyalar to‘g‘ri ishlayotganini tekshirish uchun testlarni xohlagan payt ishga tushirishingiz mumkin:

```powershell
python tests/test_all.py
python tests/test_scheduler.py
```
Testlar SQLite bazasi, FSM jarayonlari, sana va vaqt parserlari, brute-force himoyasi, takrorlanuvchi vazifalar va APScheduler ishlashini 100% tekshirib beradi.

