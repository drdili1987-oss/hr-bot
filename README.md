# HR Management & Recruiting Telegram Bot

Aiogram 3.x asosida qurilgan HR bot: rekruting (nomzod anketasi → HR guruhi) va onbording modullari.

## Struktura

```
hr_bot/
├── main.py                # Entry point
├── config.py               # .env dan sozlamalarni o'qiydi
├── database.py             # aiosqlite: candidates jadvali
├── states.py                # FSM holatlari (RecruitingForm)
├── keyboards.py             # Reply/inline klaviaturalar
├── handlers/
│   ├── start.py             # /start, menyu, "Kompaniya haqida"
│   ├── recruiting.py        # Anketa FSM: ism → tel → tajriba → rezyume
│   ├── onboarding.py        # /onboarding — bosqichma-bosqich yo'riqnoma
│   └── help.py               # /help
├── requirements.txt
└── .env.example
```

## O'rnatish

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

`.env` faylini to'ldiring:
- `BOT_TOKEN` — @BotFather'dan olingan token
- `HR_GROUP_ID` — botni HR guruhiga admin qilib qo'shing, so'ng guruh ID'sini oling
  (masalan, @userinfobot yoki botni guruhga qo'shib logdan)

## Ishga tushirish

```bash
python3 main.py
```

## Funksionallik

- `/start` — menyu: "💼 Vakansiyalarga topshirish", "ℹ️ Kompaniya haqida"
- Anketa 4 bosqichda (FSM): F.I.O → telefon (kontakt tugmasi yoki qo'lda, validatsiya bilan) →
  tajriba → rezyume (PDF/DOCX, ≤20MB, formatga tekshiriladi)
- Yakunda: ma'lumotlar SQLite'ga saqlanadi, HR guruhiga formatlangan xabar + rezyume fayli
  avtomatik yuboriladi, nomzodga tasdiq xabari qaytadi
- `/onboarding` — inline tugmalar orqali bosqichma-bosqich: qoidalar → birinchi kun → FAQ
- `/help` — buyruqlar ro'yxati

## Eslatmalar / keyingi qadamlar

- Hozircha SQLite ishlatiladi (TZ'dagi "boshlang'ich bosqich" varianti). Yuklama oshsa,
  `database.py`'ni PostgreSQL (masalan, asyncpg) ga o'tkazish tavsiya etiladi.
- Onbording matnlari (`handlers/onboarding.py`) va "Kompaniya haqida" matni (`handlers/start.py`)
  hozircha statik — real kontent bilan almashtiring.
- Production uchun: Docker konteynerga o'rash, systemd/supervisor bilan boshqarish,
  loglarni fayl/monitoring tizimiga yo'naltirish tavsiya etiladi.
