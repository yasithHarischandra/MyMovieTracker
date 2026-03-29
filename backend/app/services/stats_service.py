from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.movie import Movie
from app.models.tv_show import TvShow
from app.models.season import Season
from app.models.episode import Episode
from app.models.watch_history import WatchHistory
from app.schemas.stats import DashboardStats, MovieStats, SeriesStats, PeriodStats
from app.schemas.watch import WatchHistoryEntry


async def get_dashboard_stats(user_id: int, db: AsyncSession) -> DashboardStats:
    # ── Movie stats ──────────────────────────────────────────────────────────
    movies_watched_result = await db.execute(
        select(func.count(func.distinct(WatchHistory.movie_id)))
        .where(WatchHistory.user_id == user_id, WatchHistory.movie_id.isnot(None))
    )
    movies_watched = movies_watched_result.scalar() or 0

    movie_hours_result = await db.execute(
        select(func.sum(Movie.runtime_mins))
        .join(WatchHistory, WatchHistory.movie_id == Movie.id)
        .where(WatchHistory.user_id == user_id, WatchHistory.movie_id.isnot(None))
    )
    movie_mins = movie_hours_result.scalar() or 0

    # ── Series stats ─────────────────────────────────────────────────────────
    eps_watched_result = await db.execute(
        select(func.count(func.distinct(WatchHistory.episode_id)))
        .where(WatchHistory.user_id == user_id, WatchHistory.episode_id.isnot(None))
    )
    eps_watched = eps_watched_result.scalar() or 0

    series_mins_result = await db.execute(
        select(func.sum(func.coalesce(Episode.runtime_mins, 45)))
        .join(WatchHistory, WatchHistory.episode_id == Episode.id)
        .where(WatchHistory.user_id == user_id, WatchHistory.episode_id.isnot(None))
    )
    series_mins = series_mins_result.scalar() or 0

    # Compute show stats in-memory once we have the tree
    shows_result = await db.execute(
        select(TvShow).where(TvShow.user_id == user_id)
        .options(selectinload(TvShow.seasons).selectinload(Season.episodes))
    )
    shows = list(shows_result.scalars().all())
    
    # Watched episode IDs
    watched_ep_ids_result = await db.execute(
        select(WatchHistory.episode_id)
        .where(WatchHistory.user_id == user_id, WatchHistory.episode_id.isnot(None))
    )
    watched_ep_ids = {r.episode_id for r in watched_ep_ids_result}
    
    
    in_progress_count = 0
    remaining_eps = 0
    remaining_mins = 0
    total_eps = 0
    
    for show in shows:
        all_eps = [ep for s in show.seasons for ep in s.episodes]
        if not all_eps:
            continue
            
        total_eps += len(all_eps)
        all_ep_ids = {ep.id for ep in all_eps}
        w = len(all_ep_ids & watched_ep_ids)
        
        # In-progress means started but not finished
        if 0 < w < len(all_ep_ids):
            in_progress_count += 1
            
        # Compute remaining stats for ALL shows (so watched + remaining = total)
        # Using pure Python properly handles the fallback to 45 mins for missing runtimes
        if w < len(all_ep_ids):
            for ep in all_eps:
                if ep.id not in watched_ep_ids:
                    remaining_eps += 1
                    remaining_mins += ep.runtime_mins or 45

    completion_pct = round((len(watched_ep_ids) / total_eps) * 100, 1) if total_eps > 0 else 0

    return DashboardStats(
        movies=MovieStats(
            movies_watched=movies_watched,
            movie_hours_watched=round(movie_mins / 60, 1),
        ),
        series=SeriesStats(
            episodes_watched=eps_watched,
            series_hours_watched=round(series_mins / 60, 1),
            in_progress_count=in_progress_count,
            total_episodes_tracked=total_eps,
            remaining_episodes=max(remaining_eps, 0),
            remaining_hours=round(remaining_mins / 60, 1),
            completion_pct=completion_pct,
        ),
    )


async def get_period_stats(
    user_id: int,
    from_dt: datetime,
    to_dt: datetime,
    db: AsyncSession,
) -> PeriodStats:
    movies_result = await db.execute(
        select(func.count(func.distinct(WatchHistory.movie_id)))
        .where(
            WatchHistory.user_id == user_id,
            WatchHistory.movie_id.isnot(None),
            WatchHistory.watched_at >= from_dt,
            WatchHistory.watched_at <= to_dt,
        )
    )
    movies_watched = movies_result.scalar() or 0

    movie_mins_result = await db.execute(
        select(func.sum(Movie.runtime_mins))
        .join(WatchHistory, WatchHistory.movie_id == Movie.id)
        .where(
            WatchHistory.user_id == user_id,
            WatchHistory.watched_at >= from_dt,
            WatchHistory.watched_at <= to_dt,
        )
    )
    movie_mins = movie_mins_result.scalar() or 0

    eps_result = await db.execute(
        select(func.count(func.distinct(WatchHistory.episode_id)))
        .where(
            WatchHistory.user_id == user_id,
            WatchHistory.episode_id.isnot(None),
            WatchHistory.watched_at >= from_dt,
            WatchHistory.watched_at <= to_dt,
        )
    )
    eps_watched = eps_result.scalar() or 0

    series_mins_result = await db.execute(
        select(func.sum(func.coalesce(Episode.runtime_mins, 45)))
        .join(WatchHistory, WatchHistory.episode_id == Episode.id)
        .where(
            WatchHistory.user_id == user_id,
            WatchHistory.watched_at >= from_dt,
            WatchHistory.watched_at <= to_dt,
        )
    )
    series_mins = series_mins_result.scalar() or 0

    movie_hours = round(movie_mins / 60, 1)
    series_hours = round(series_mins / 60, 1)

    return PeriodStats(
        movies_watched=movies_watched,
        movie_hours=movie_hours,
        episodes_watched=eps_watched,
        series_hours=series_hours,
        total_hours=round(movie_hours + series_hours, 1),
    )


async def get_watch_history(
    user_id: int,
    db: AsyncSession,
    limit: int = 50,
    offset: int = 0,
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
) -> list[WatchHistoryEntry]:
    query = (
        select(WatchHistory)
        .options(
            selectinload(WatchHistory.movie),
            selectinload(WatchHistory.episode).selectinload(Episode.season).selectinload(Season.show)
        )
        .where(WatchHistory.user_id == user_id)
        .order_by(WatchHistory.watched_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if from_dt:
        query = query.where(WatchHistory.watched_at >= from_dt)
    if to_dt:
        query = query.where(WatchHistory.watched_at <= to_dt)

    result = await db.execute(query)
    entries = list(result.scalars().all())

    # Enrich with media metadata
    output = []
    for e in entries:
        item = WatchHistoryEntry(
            id=e.id,
            watched_at=e.watched_at,
            rating=e.rating,
            note=e.note,
            movie_id=e.movie_id,
            episode_id=e.episode_id,
        )
        if e.movie_id and e.movie:
            item.movie_title = e.movie.title
            item.movie_poster_path = e.movie.poster_path
            item.movie_runtime_mins = e.movie.runtime_mins
        if e.episode_id and e.episode:
            ep = e.episode
            season = ep.season
            show = season.show if season else None
            item.show_id = show.id if show else None
            item.show_name = show.name if show else None
            item.show_poster_path = show.poster_path if show else None
            item.season_number = season.season_number if season else None
            item.episode_number = ep.episode_number
            item.episode_name = ep.name
            item.episode_runtime_mins = ep.runtime_mins
        output.append(item)
    return output
