"""APScheduler process entrypoint. Run with `python -m app.workers.scheduler`.

Must stay single-instance (see docker-compose.yml comments) - running more
than one replica double-enqueues every scheduled task.

Design: rather than one APScheduler job per job_source (which would need
rescheduling every time a source is added/edited/deleted), a single sweep
runs every SCHEDULER_SWEEP_INTERVAL_MINUTES and enqueues `poll_source` for
any source whose own poll_interval_minutes has elapsed since
last_polled_at. Per-source frequency is then just a config value on the
row, not a separate scheduled job.
"""
from datetime import datetime, timedelta, timezone

import structlog
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select

from app.config import get_settings
from app.database import get_sync_session
from app.models.job import JobSource
from app.workers.queue import default_queue, llm_queue

log = structlog.get_logger()
settings = get_settings()


def sweep_job_sources() -> None:
    now = datetime.now(timezone.utc)
    with get_sync_session() as db:
        sources = db.execute(select(JobSource).where(JobSource.is_active.is_(True))).scalars().all()
        due = [
            s
            for s in sources
            if s.last_polled_at is None
            or s.last_polled_at + timedelta(minutes=s.poll_interval_minutes) <= now
        ]

    log.info("scheduler.sweep", total_sources=len(sources), due=len(due))
    for source in due:
        default_queue().enqueue("app.workers.ingestion_tasks.poll_source", str(source.id))


def refresh_salary_snapshots() -> None:
    llm_queue().enqueue("app.workers.salary_tasks.refresh_all_salary_snapshots")


def main() -> None:
    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(
        sweep_job_sources,
        trigger=IntervalTrigger(minutes=settings.scheduler_sweep_interval_minutes),
        id="sweep_job_sources",
        next_run_time=datetime.now(timezone.utc),  # run once immediately on boot
    )
    scheduler.add_job(
        refresh_salary_snapshots,
        trigger=CronTrigger(hour=settings.salary_refresh_cron_hour, minute=0),
        id="refresh_salary_snapshots",
    )
    log.info("scheduler.starting")
    scheduler.start()


if __name__ == "__main__":
    main()
