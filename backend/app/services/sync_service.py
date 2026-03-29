import asyncio
import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import AsyncSessionLocal
from app.models.tv_show import TvShow
from app.models.season import Season
from app.models.episode import Episode
from app.services import tmdb_service
from datetime import date as date_type

logger = logging.getLogger(__name__)


async def sync_returning_shows() -> dict:
    """Background job: sync new episodes for all Returning Series shows across all users."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(TvShow)
            .where(TvShow.status == "Returning Series")
            .options(selectinload(TvShow.seasons).selectinload(Season.episodes))
        )
        shows = list(result.scalars().all())

    updated, errors = 0, 0
    for show in shows:
        try:
            await _sync_one_show(show.id)
            updated += 1
            await asyncio.sleep(0.5)  # gentle rate-limiting against TMDB
        except Exception as exc:
            logger.error(f"Sync failed for show id={show.id} tmdb_id={show.tmdb_id}: {exc}")
            errors += 1

    logger.info(f"TMDB sync complete: {updated} updated, {errors} errors")
    return {"updated": updated, "errors": errors}


async def _sync_one_show(show_id: int) -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(TvShow)
            .where(TvShow.id == show_id)
            .options(selectinload(TvShow.seasons).selectinload(Season.episodes))
        )
        show = result.scalar_one_or_none()
        if not show:
            return

        data = await tmdb_service.get_show_update(show.tmdb_id)

        existing_seasons = {s.season_number: s for s in show.seasons}

        def _parse_date(s):
            if isinstance(s, str) and s:
                try:
                    return date_type.fromisoformat(s)
                except ValueError:
                    return None
            return None

        for s_data in data.get("seasons", []):
            sn = s_data["season_number"]
            if sn in existing_seasons:
                season = existing_seasons[sn]
                # Add any new episodes
                existing_ep_nums = {ep.episode_number for ep in season.episodes}
                for ep_data in s_data.get("episodes", []):
                    if ep_data["episode_number"] not in existing_ep_nums:
                        db.add(Episode(
                            season_id=season.id,
                            episode_number=ep_data["episode_number"],
                            name=ep_data.get("name"),
                            runtime_mins=ep_data.get("runtime_mins", 45),
                            air_date=_parse_date(ep_data.get("air_date")),
                        ))
                season.episode_count = len(s_data.get("episodes", []))
            else:
                # New season
                season = Season(
                    show_id=show.id,
                    season_number=sn,
                    name=s_data.get("name"),
                    episode_count=s_data.get("episode_count", 0),
                    air_date=_parse_date(s_data.get("air_date")),
                )
                db.add(season)
                await db.flush()
                for ep_data in s_data.get("episodes", []):
                    db.add(Episode(
                        season_id=season.id,
                        episode_number=ep_data["episode_number"],
                        name=ep_data.get("name"),
                        runtime_mins=ep_data.get("runtime_mins", 45),
                        air_date=_parse_date(ep_data.get("air_date")),
                    ))

        # Update show status and sync timestamp
        show.status = data.get("status", show.status)
        show.last_synced_at = datetime.now(timezone.utc)
        await db.commit()
