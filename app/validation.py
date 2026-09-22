from __future__ import annotations

from datetime import date
from pathlib import Path

from app.models import CalendarEvent


class ValidationError(Exception):
    pass


def validate_events(events: list[CalendarEvent], target: date) -> None:
    if not isinstance(events, list):
        raise ValidationError("invalid event list")
    for ev in events:
        if ev.importance not in (1, 2, 3):
            raise ValidationError(f"invalid importance: {ev.importance}")
        if ev.dt_tehran.tzinfo is None:
            raise ValidationError("tehran time missing tzinfo")
        if ev.currency and len(ev.currency) > 4:
            raise ValidationError(f"invalid currency: {ev.currency}")


def validate_images(paths: list[Path]) -> None:
    if not paths:
        raise ValidationError("no image generated")
    for path in paths:
        if not path.exists() or path.stat().st_size < 4000:
            raise ValidationError(f"image missing or too small: {path}")
        if path.stat().st_size > 9_500_000:
            raise ValidationError(f"image too large for Telegram: {path}")
