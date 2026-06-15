"""APScheduler: ежедневная проверка сроков и отправка дайджеста."""
from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.database import SessionLocal
from app.services import notifier

logger = logging.getLogger(__name__)
_scheduler: BackgroundScheduler | None = None


def _daily_job() -> None:
    with SessionLocal() as db:
        notifier.run_digest(db)


def start_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler
    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(
        _daily_job,
        CronTrigger(hour=settings.digest_hour, minute=0),
        id="daily_digest",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("Scheduler запущен: ежедневный дайджест в %02d:00", settings.digest_hour)
    return _scheduler


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
