from __future__ import annotations

from datetime import date

from app.models import CalendarEvent

VALID_CCY = {"USD", "EUR", "GBP", "JPY", "CAD", "AUD", "NZD", "CHF", "CNY"}


def filter_events(
    events: list[CalendarEvent],
    target: date,
    min_importance: int,
    currencies: list[str],
) -> list[CalendarEvent]:
    allowed = {c.upper() for c in currencies}
    out: list[CalendarEvent] = []
    for ev in events:
        if ev.dt_tehran.date() != target:
            continue
        if ev.importance < min_importance:
            continue
        if ev.currency.upper() not in allowed:
            continue
        if ev.currency.upper() not in VALID_CCY:
            continue
        if ev.importance not in (1, 2, 3):
            continue
        out.append(ev)
    out.sort(key=lambda e: (e.dt_tehran, -e.importance, e.title_en.lower()))
    return out
