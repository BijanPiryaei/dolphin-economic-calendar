from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from app.calendar_api import CalendarClient, CalendarFetchError
from app.database import Store, events_hash
from app.filters import filter_events
from app.formatter import jalali_long
from app.renderer import render_calendar
from app.telegram_bot import TelegramClient, TelegramError
from app.translator import Translator
from app.validation import ValidationError, validate_events, validate_images


class Pipeline:
    def __init__(self, settings, logger) -> None:
        self.settings = settings
        self.logger = logger
        self.translator = Translator(settings.root / "data" / "translations.json")
        self.client = CalendarClient(settings, self.translator, settings.root / "data" / "fixtures")
        self.store = Store(settings.root / "data" / "app.db")
        self.tg = TelegramClient(settings.telegram_bot_token, settings.telegram_channel_id)

    def target_date(self, which: str) -> date:
        today = date.today()
        if which == "today":
            return today
        return today + timedelta(days=1)

    def generate(self, which: str = "tomorrow") -> tuple[date, list[Path], list]:
        target = self.target_date(which)
        self.logger.info("Fetching calendar for %s", target)
        raw = self.client.fetch(target)
        self.logger.info("%s events received", len(raw))
        events = filter_events(raw, target, self.settings.min_importance, self.settings.enabled_currencies)
        self.logger.info("%s events passed filters", len(events))
        validate_events(events, target)
        out_dir = self.settings.root / "generated"
        paths = render_calendar(events, target, self.settings, out_dir)
        validate_images(paths)
        self.logger.info("Image generated: %s", ", ".join(str(p.name) for p in paths))
        return target, paths, events

    def publish(self, which: str = "tomorrow", force: bool = False) -> str:
        target, paths, events = self.generate(which)
        payload = [e.to_dict() for e in events]
        digest = events_hash(payload)
        row = self.store.get(target.isoformat())
        if row and row["status"] == "sent" and row["data_hash"] == digest and not force and not self.settings.enable_update_mode:
            self.logger.info("Duplicate prevented for %s", target)
            return "duplicate"
        caption = self._caption(target, events)
        msg_id = self.tg.send_media_group(paths, caption)
        self.store.upsert(target.isoformat(), "sent", len(events), str(paths[0]), msg_id, digest)
        self.logger.info("Telegram post successful id=%s", msg_id)
        return msg_id

    def alert(self, text: str) -> None:
        if not self.settings.enable_admin_alerts:
            return
        for admin in self.settings.admin_user_ids:
            try:
                self.tg.send_message(admin, text)
            except TelegramError as exc:
                self.logger.error("admin alert failed: %s", exc)

    def _caption(self, target: date, events: list) -> str:
        highs = sum(1 for e in events if e.importance == 3)
               return (
            f"📊 تقویم اقتصادی فردا\n"
            f"📅 {jalali_long(target)}\n"
            f"⏰ زمان‌ها: ساعت تهران\n\n"
            f"🔴 بسیارمهم: {highs}\n"
            f"🟠 مهم / 🔵 معمولی\n\n"
            f"منبع رویدادها: تقویم عمومی بازار (Forex Factory)\n"
            f"توصیه مالی نیست\n\n"
            f"🌐 سایت: https://dolphintraders.ir\n"
            f"📅 تقویم اقتصادی: https://t.me/DolphinTraders_ir\n"
            f"💱 نرخ لحظه‌ای: https://t.me/ForexPreice"
        )


def run_safe(pipeline: Pipeline, which: str, preview: bool, force: bool = False) -> None:
    try:
        if preview:
            pipeline.generate(which)
            return
        pipeline.publish(which, force=force)
    except (CalendarFetchError, ValidationError, TelegramError, Exception) as exc:
        pipeline.logger.error("Calendar generation failed: %s", exc)
        pipeline.alert(
            "🚨 Dolfin Traders Calendar Bot\n\n"
            f"Calendar generation failed.\nDate mode: {which}\nError: {exc}"
        )
        raise
