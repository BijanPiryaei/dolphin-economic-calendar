from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import requests

TEHRAN = ZoneInfo("Asia/Tehran")

SYMBOLS = [
    ("XAUUSD", "🇺🇸", "طلا", "GC=F", None),
    ("XAGUSD", "🇺🇸", "نقره", "SI=F", None),
    ("BTCUSD", "🇺🇸", "بیت‌کوین", "BTC-USD", "BTCUSDT"),
    ("ETHUSD", "🇺🇸", "اتریوم", "ETH-USD", "ETHUSDT"),
    ("GBPUSD", "🇬🇧", "پوند / دلار", "GBPUSD=X", None),
    ("EURUSD", "🇪🇺", "یورو / دلار", "EURUSD=X", None),
    ("AUDUSD", "🇦🇺", "استرالیا / دلار", "AUDUSD=X", None),
    ("NZDUSD", "🇳🇿", "نیوزلند / دلار", "NZDUSD=X", None),
    ("USDJPY", "🇯🇵", "دلار / ین", "USDJPY=X", None),
    ("USDCAD", "🇨🇦", "دلار / کانادا", "USDCAD=X", None),
]


def _fmt(value: float, digits: int) -> str:
    if value >= 100:
        return f"{value:,.2f}"
    if digits == 0:
        return f"{value:,.0f}"
    return f"{value:.{digits}f}"


def _digits(symbol: str) -> int:
    if symbol in {"BTCUSD"}:
        return 0
    if symbol in {"ETHUSD", "XAUUSD"}:
        return 2
    if symbol == "XAGUSD":
        return 3
    if symbol == "USDJPY":
        return 3
    return 5


def _yahoo(ticker: str) -> float | None:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    headers = {"User-Agent": "Mozilla/5.0 DolphinTraders/1.0"}
    try:
        r = requests.get(url, params={"range": "1d", "interval": "1m"}, headers=headers, timeout=12)
        r.raise_for_status()
        result = r.json()["chart"]["result"][0]
        meta = result.get("meta") or {}
        price = meta.get("regularMarketPrice")
        if price is None:
            quotes = (result.get("indicators") or {}).get("quote") or [{}]
            closes = quotes[0].get("close") or []
            price = next((c for c in reversed(closes) if c is not None), None)
        return float(price) if price is not None else None
    except Exception:
        return None


def _binance(symbol: str) -> float | None:
    url = "https://api.binance.com/api/v3/ticker/price"
    try:
        r = requests.get(url, params={"symbol": symbol}, timeout=10)
        r.raise_for_status()
        return float(r.json()["price"])
    except Exception:
        return None


def fetch_quotes() -> list[dict]:
    rows = []
    for key, emoji, name, yahoo, binance in SYMBOLS:
        price = _binance(binance) if binance else None
        if price is None:
            price = _yahoo(yahoo)
        rows.append(
            {
                "key": key,
                "emoji": emoji,
                "name": name,
                "price": price,
                "digits": _digits(key),
            }
        )
    return rows


FOOTER = (
    "🌐 سایت: https://dolphintraders.ir\n"
    "📅 تقویم اقتصادی: https://t.me/DolphinTraders_ir\n"
    "💱 نرخ لحظه‌ای: https://t.me/ForexPreice"
)


def format_message(rows: list[dict]) -> str:
    now = datetime.now(TEHRAN).strftime("%H:%M:%S")
    lines = [
        "🐬 <b>Dolphin Traders</b>",
        "نرخ تقریبی بازار",
        "────────────",
    ]
    blocks = []
    for row in rows:
        if row["price"] is None:
            val = "—"
        else:
            val = _fmt(row["price"], row["digits"])
        blocks.append(f"{row['emoji']} {row['name']}\n\u2066{val}\u2069")
    lines.append("\n────────────\n".join(blocks))
    lines.extend(
        [
            "────────────",
            f"🕐 تهران {now}",
            "منبع طلا، نقره و فارکس: Yahoo Finance",
            "منبع بیت‌کوین و اتریوم: Binance",
            "تأخیر دارد · توصیه مالی نیست",
            FOOTER,
        ]
    )
    return "\n".join(lines)    return "\n".join(lines)
