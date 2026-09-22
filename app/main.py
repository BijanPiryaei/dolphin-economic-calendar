from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import load_settings
from app.logger import setup_logger
from app.pipeline import Pipeline, run_safe
from app.scheduler import start_scheduler


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Dolfin Traders economic calendar bot")
    p.add_argument("--date", choices=["today", "tomorrow"], default="tomorrow")
    p.add_argument("--preview", action="store_true")
    p.add_argument("--send", action="store_true")
    p.add_argument("--force", action="store_true")
    p.add_argument("--telegram-test", action="store_true")
    p.add_argument("--schedule", action="store_true")
    p.add_argument("--admin-bot", action="store_true")
    return p


def main() -> int:
    args = build_parser().parse_args()
    settings = load_settings()
    logger = setup_logger(settings.root / "logs", settings.log_level)
    pipeline = Pipeline(settings, logger)

    if args.telegram_test:
        pipeline.tg.send_message(settings.telegram_channel_id, "✅ تست اتصال ربات Dolfin Traders")
        logger.info("Telegram test sent")
        return 0
    if args.schedule:
        start_scheduler(pipeline)
        return 0
    if args.admin_bot:
        from app.admin_bot import run_admin_bot

        run_admin_bot(pipeline)
        return 0
    preview = args.preview or not args.send
    run_safe(pipeline, args.date, preview=preview, force=args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
