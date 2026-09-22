from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

TEHRAN = ZoneInfo("Asia/Tehran")


def parse_api_datetime(value: str, assume_utc: bool = True) -> datetime:
    raw = (value or "").strip()
    if not raw:
        raise ValueError("empty datetime")
    raw = raw.replace("Z", "+00:00")
    if "T" not in raw and " " in raw:
        raw = raw.replace(" ", "T", 1)
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc if assume_utc else TEHRAN)
    return dt.astimezone(timezone.utc)


def to_tehran(dt_utc: datetime) -> datetime:
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
    return dt_utc.astimezone(TEHRAN)


def format_tehran_clock(dt_tehran: datetime) -> str:
    return dt_tehran.strftime("%H:%M")
