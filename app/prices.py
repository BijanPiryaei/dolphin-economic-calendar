from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import requests

TEHRAN = ZoneInfo("Asia/Tehran")

SYMBOLS = [
    ("XAUUSD", "🇺🇸", "طلا", None, None, "XAU"),
    ("XAGUSD", "🇺🇸", "نقره", None, None, "XAG"),
    ("BTCUSD", "🇺🇸", "بیت‌کوین", "BTC-USD", "BTCUSDT", None),
    ("ETHUSD", "🇺🇸", "اتریوم", "ETH-USD", "ETHUSDT", None),
    ("GBPUSD", "🇬🇧", "پوند به دلار", "GBPUSD=X", None, None),
    ("EURUSD", "🇪🇺", "یورو به دلار", "EURUSD=X", None, None),
    ("AUDUSD", "🇦🇺", "استرالیا به دلار", "AUDUSD=X", None, None),
    ("NZDUSD", "🇳🇿", "نیوزلند به دلار", "NZDUSD=X", None, None),
    ("JPYUSD", "🇯🇵", "ین به دلار", "USDJPY=X", None, None),
    ("CADUSD", "🇨🇦", "کانادا به دلار", "CADUSD=X", None, None),
]


def _fmt(value: float, digits: int) -> str:
    if value >= 100:
        return f"{value:,.2f}"
    if digits == 0:
        return f"{value:,.0f}"
    return f"{value:.{digits}f}"


def _digits(symbol: str) -> int:
    if symbol == "BTCUSD":
        return 0
    if symbol in {"ETHUSD", "XAUUSD"}:
        return 2
    if symbol == "XAGUSD":
        return 3
    if symbol == "JPYUSD":
        return 6
    return 5


def _metal(symbol: str) -> float | None:
    try:
        r = requests.get(f"https://api.gold-api.com/price/{symbol}", timeout=12)
        r.raise_for_status()
        return float(r.json()["price"])
    except Exception:
        return None


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
        data = r.json()
        if "price" not in data:
            return None
        return float(data["price"])
    except Exception:
        return None


def fetch_quotes() -> list[dict]:
    rows = []
    for key, emoji, name, yahoo, binance, metal in SYMBOLS:
        price = None
        if metal:
            price = _metal(metal)
            if price is None:
                price = _yahoo("GC=F" if metal == "XAU" else "SI=F")
        if price is None and binance:
            price = _binance(binance)
        if price is None and yahoo:
            price = _yahoo(yahoo)
        if price and key == "JPYUSD":
            price = 1.0 / price
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


def _slot_clock() -> str:
    return datetime.now(TEHRAN).strftime("%H:%M:%S")

def format_message(rows: list[dict]) -> str:
    clock = _slot_clock()
    lines = [
        "🐬 <b>Dolphin Traders</b>",
        f"نرخ تقریبی بازار  {clock}",
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
            f"🕐 تهران {clock}",
            "طلا و نقره: قیمت اسپات",
            "فارکس: Yahoo Finance",
            "بیت‌کوین و اتریوم: Binance / Yahoo",
            "با نرخ بروکر یکی نیست · توصیه مالی نیست",
            FOOTER,
        ]
    )
    return "\n".join(lines)
