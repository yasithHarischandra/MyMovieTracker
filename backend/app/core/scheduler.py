from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = AsyncIOScheduler()


def setup_scheduler() -> None:
    """Register all background jobs. Called once at app startup."""
    from app.services.sync_service import sync_returning_shows  # avoid circular import

    scheduler.add_job(
        sync_returning_shows,
        trigger=CronTrigger(day_of_week="tue,fri", hour=2, minute=0, timezone="UTC"),
        id="tmdb_sync",
        name="TMDB Returning Series Sync",
        replace_existing=True,
        misfire_grace_time=3600,  # allow up to 1h late if server was down
    )
