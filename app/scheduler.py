from __future__ import annotations

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from zoneinfo import ZoneInfo

from app.pipeline import run_safe


def start_scheduler(pipeline) -> None:
    hour, minute = pipeline.settings.post_time.split(":")
    tz = ZoneInfo(pipeline.settings.timezone)
    sched = BlockingScheduler(timezone=tz)
    sched.add_job(
        lambda: run_safe(pipeline, "tomorrow", preview=False),
        CronTrigger(hour=int(hour), minute=int(minute), timezone=tz),
        id="nightly_calendar",
        max_instances=1,
        coalesce=True,
    )
    pipeline.logger.info("Scheduler started at %s %s", pipeline.settings.post_time, pipeline.settings.timezone)
    sched.start()
