# Dolfin Traders — ربات تقویم اقتصادی تلگرام

هر شب تقویم اقتصادی **فردا** را از API می‌گیرد، به وقت تهران و فارسی آماده می‌کند، تصویر برندشده می‌سازد و در کانال تلگرام منتشر می‌کند.

تصویر نمونه بنفش Dolphin Traders به‌عنوان مرجع طراحی استفاده شده است.

> تلگرام سرور اجرای ربات نمی‌دهد. ربات باید روی VPS یا سیستم خودتان اجرا شود و فقط از Bot API تلگرام عکس بفرستد.

دامنه درست سایت: https://dolphintraders.ir

## Features

- منبع داده: Trading Economics (اصلی) / Finnhub / Mock برای تست
- بدون حدس داده؛ اگر API خطا بدهد منتشر نمی‌شود
- تبدیل زمان با `zoneinfo` به `Asia/Tehran` (DST درست است)
- تاریخ شمسی با `jdatetime`
- ترجمه Eventها از `data/translations.json` نه LLM
- فیلتر اهمیت و ارز از `.env`
- تصویر داینامیک با Pillow + RTL فارسی
- جلوگیری از ارسال تکراری با SQLite
- Retry، لاگ، هشدار ادمین
- Preview بدون ارسال تلگرام
- Docker و Scheduler

## API

| Provider | هزینه | نکته |
|---|---|---|
| `mock` | رایگان | برای preview و تست |
| Trading Economics | پولی | `GET /calendar/country/all/{from}/{to}?c=KEY` زمان UTC، Importance ۱/۲/۳ |
| Finnhub `/calendar/economic` | پلن Premium | impact: low/medium/high |

نسخه اول را با `API_PROVIDER=mock` تست کنید. برای انتشار واقعی کلید Trading Economics بگذارید.

## نصب محلی

```bash
cd dolfin-economic-calendar
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

لوگو اختیاری: `assets/logo.png`

## اجرا

```bash
# فقط تصویر
python -m app.main --preview --date tomorrow

# ارسال به کانال
python -m app.main --send --date tomorrow

# تست پیام تلگرام
python -m app.main --telegram-test

# زمان‌بندی ۲۲:۰۰ تهران
python -m app.main --schedule

# دستورات ادمین
python -m app.main --admin-bot
```

ربات را Admin کانال کنید با حق ارسال پیام.

دستورات ادمین فقط برای `ADMIN_USER_IDS`: `/start /status /preview /send /tomorrow /today`

## Docker

```bash
cp .env.example .env
docker compose up -d
```

## امنیت

`.env` را commit نکنید. توکن را در چت عمومی نفرستید.

## Troubleshooting

- تصویر ساخته نمی‌شود: فونت‌های `assets/fonts` را چک کنید
- تلگرام خطا می‌دهد: Bot را Admin کنید و `TELEGRAM_CHANNEL_ID` را با `@channel` یا id عددی بگذارید
- داده خالی: `MIN_IMPORTANCE` را کم کنید یا provider را `mock` بگذارید
- ارسال تکراری: عادی است؛ `--force` برای ارسال مجدد
