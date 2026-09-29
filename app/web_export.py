from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.formatter import jalali_long
from app.models import CalendarEvent

TEHRAN = ZoneInfo("Asia/Tehran")
IMPACT = {3: "بسیارمهم", 2: "مهم", 1: "معمولی"}


def _event_row(ev: CalendarEvent) -> dict:
    clock = ev.dt_tehran.strftime("%H:%M") if ev.dt_tehran else "--:--"
    return {
        "time": clock,
        "currency": ev.currency,
        "title": ev.title,
        "title_en": ev.title_en,
        "importance": ev.importance,
        "importance_fa": IMPACT.get(ev.importance, "معمولی"),
        "actual": ev.actual or "-",
        "forecast": ev.forecast or "-",
        "previous": ev.previous or "-",
    }


def _day_block(target: date, events: list[CalendarEvent]) -> dict:
    return {
        "date": target.isoformat(),
        "jalali": jalali_long(target),
        "events": [_event_row(e) for e in events],
    }


def write_web_calendar(
    path: Path,
    today: date,
    today_events: list[CalendarEvent],
    tomorrow: date,
    tomorrow_events: list[CalendarEvent],
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated_at": datetime.now(TEHRAN).isoformat(timespec="seconds"),
        "timezone": "Asia/Tehran",
        "source": "Forex Factory public calendar",
        "disclaimer": "توصیه مالی نیست",
        "today": _day_block(today, today_events),
        "tomorrow": _day_block(tomorrow, tomorrow_events),
        "site": "https://dolphintraders.ir",
        "telegram": "https://t.me/DolphinTraders_ir",
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
