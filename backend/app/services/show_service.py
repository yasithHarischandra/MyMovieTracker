from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from datetime import date as date_type, datetime

from app.models.tv_show import TvShow
from app.models.season import Season
from app.models.episode import Episode
from app.models.watch_history import WatchHistory
from app.schemas.watch import WatchCreate
from app.schemas.tv_show import InProgressShow, EpisodeResponse
from app.services import tmdb_service


async def _get_show_owned(show_id: int, user_id: int, db: AsyncSession) -> TvShow:
    result = await db.execute(
        select(TvShow)
        .where(TvShow.id == show_id, TvShow.user_id == user_id)
        .options(selectinload(TvShow.seasons).selectinload(Season.episodes))
    )
    show = result.scalar_one_or_none()
    if not show:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Show not found")
    return show


async def add_show(tmdb_id: int, user_id: int, db: AsyncSession) -> TvShow:
    result = await db.execute(
        select(TvShow).where(TvShow.tmdb_id == tmdb_id, TvShow.user_id == user_id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Show already in library")

    try:
        data = await tmdb_service.get_show_detail(tmdb_id)
        # Handle case where TMDB ID might have changed (normalized)
        new_tmdb_id = data["tmdb_id"]
        if new_tmdb_id != tmdb_id:
            result = await db.execute(
                select(TvShow).where(TvShow.tmdb_id == new_tmdb_id, TvShow.user_id == user_id)
            )
            if result.scalar_one_or_none():
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Show already in library (ID normalization)")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to fetch show from TMDB")

    def _parse_date(s):
        if isinstance(s, str) and s:
            try:
                return date_type.fromisoformat(s)
            except ValueError:
                return None
        return None

    show = TvShow(
        tmdb_id=data["tmdb_id"],
        user_id=user_id,
        name=data["name"],
        overview=data.get("overview"),
        first_air_date=_parse_date(data.get("first_air_date")),
        genres=data.get("genres"),
        status=data.get("status"),
        poster_path=data.get("poster_path"),
    )
    db.add(show)
    await db.flush()  # get show.id

    for s_data in data.get("seasons", []):
        season = Season(
            show_id=show.id,
            season_number=s_data["season_number"],
            name=s_data.get("name"),
            episode_count=s_data.get("episode_count", 0),
            air_date=_parse_date(s_data.get("air_date")),
        )
        db.add(season)
        await db.flush()

        for ep in s_data.get("episodes", []):
            episode = Episode(
                season_id=season.id,
                episode_number=ep["episode_number"],
                name=ep.get("name"),
                runtime_mins=ep.get("runtime_mins", 45),
                air_date=_parse_date(ep.get("air_date")),
            )
            db.add(episode)

    try:
        await db.commit()
        await db.refresh(show)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Show already in library")
    return show


async def get_show_with_progress(show_id: int, user_id: int, db: AsyncSession) -> dict:
    show = await _get_show_owned(show_id, user_id, db)

    # Fetch watched episode IDs for this show's user
    all_ep_ids = [ep.id for s in show.seasons for ep in s.episodes]
    watched_result = await db.execute(
        select(WatchHistory.episode_id, WatchHistory.id)
        .where(
            WatchHistory.user_id == user_id,
            WatchHistory.episode_id.in_(all_ep_ids),
        )
    )
    watched_map = {row.episode_id: row.id for row in watched_result}

    return {"show": show, "watched_map": watched_map}


async def mark_episode_watched(
    show_id: int, episode_id: int, user_id: int, watch_data: WatchCreate, db: AsyncSession
) -> WatchHistory:
    show = await _get_show_owned(show_id, user_id, db)
    ep_ids = {ep.id for s in show.seasons for ep in s.episodes}
    if episode_id not in ep_ids:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Episode not found in this show")

    entry = WatchHistory(user_id=user_id, episode_id=episode_id, rating=watch_data.rating, note=watch_data.note)
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def mark_next_episode_watched(show_id: int, user_id: int, db: AsyncSession) -> WatchHistory:
    show = await _get_show_owned(show_id, user_id, db)
    
    # Get watched IDs
    all_ep_ids = [ep.id for s in show.seasons for ep in s.episodes]
    watched_result = await db.execute(
        select(WatchHistory.episode_id).where(
            WatchHistory.user_id == user_id,
            WatchHistory.episode_id.in_(all_ep_ids),
        )
    )
    watched_ids = {r.episode_id for r in watched_result}
    
    next_ep = find_next_episode(show, watched_ids)
    if not next_ep:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No more episodes to watch")
        
    entry = WatchHistory(user_id=user_id, episode_id=next_ep.id)
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def mark_season_watched(
    show_id: int, season_number: int, user_id: int, db: AsyncSession
) -> list[WatchHistory]:
    show = await _get_show_owned(show_id, user_id, db)
    season = next((s for s in show.seasons if s.season_number == season_number), None)
    if not season:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Season not found")

    # Find already watched episode IDs to avoid duplicates
    ep_ids = [ep.id for ep in season.episodes]
    watched_result = await db.execute(
        select(WatchHistory.episode_id).where(
            WatchHistory.user_id == user_id,
            WatchHistory.episode_id.in_(ep_ids),
        )
    )
    already_watched = {row.episode_id for row in watched_result}

    entries = []
    for ep in season.episodes:
        if ep.id not in already_watched:
            entry = WatchHistory(user_id=user_id, episode_id=ep.id)
            db.add(entry)
            entries.append(entry)
    await db.commit()
    return entries


async def unwatch_episode(watch_history_id: int, user_id: int, db: AsyncSession) -> None:
    result = await db.execute(
        select(WatchHistory).where(
            WatchHistory.id == watch_history_id,
            WatchHistory.user_id == user_id,
            WatchHistory.episode_id.isnot(None),
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watch entry not found")
    await db.delete(entry)
    await db.commit()


async def pickup_show(show_id: int, user_id: int, db: AsyncSession) -> TvShow:
    show = await _get_show_owned(show_id, user_id, db)
    show.is_dropped = False
    await db.commit()
    await db.refresh(show)
    return show


async def drop_show(show_id: int, user_id: int, db: AsyncSession) -> TvShow:
    show = await _get_show_owned(show_id, user_id, db)
    show.is_dropped = True
    await db.commit()
    await db.refresh(show)
    return show


def find_next_episode(show: TvShow, watched_ids: set[int]) -> Optional[Episode]:
    """Finds the first unwatched episode in a show."""
    for s in sorted(show.seasons, key=lambda x: x.season_number):
        for ep in sorted(s.episodes, key=lambda x: x.episode_number):
            if ep.id not in watched_ids:
                return ep
    return None


async def get_in_progress(user_id: int, db: AsyncSession, include_dropped: bool = False) -> list[InProgressShow]:
    # Get all shows for the user
    query = select(TvShow).where(TvShow.user_id == user_id)
    if not include_dropped:
        query = query.where(TvShow.is_dropped == False)
        
    shows_result = await db.execute(
        query.options(selectinload(TvShow.seasons).selectinload(Season.episodes))
    )
    shows = list(shows_result.scalars().all())

    # Fetch all watched episodes for this user across all their shows
    # to avoid N+1 queries.
    watched_q = (
        select(WatchHistory.episode_id, WatchHistory.watched_at, Season.show_id)
        .join(Episode, WatchHistory.episode_id == Episode.id)
        .join(Season, Episode.season_id == Season.id)
        .where(WatchHistory.user_id == user_id)
    )
    watched_rows = (await db.execute(watched_q)).all()
    
    # show_id -> list of (episode_id, watched_at)
    show_watched_map = {}
    for row in watched_rows:
        show_watched_map.setdefault(row.show_id, []).append((row.episode_id, row.watched_at))

    in_progress = []
    for show in shows:
        all_ep_ids = [ep.id for s in show.seasons for ep in s.episodes]
        if not all_ep_ids:
            continue

        show_watched_entries = show_watched_map.get(show.id, [])
        watched_ids = {e[0] for e in show_watched_entries}
        watched_count = len(watched_ids)

        if watched_count == 0:
            continue  # Not started

        total = len(all_ep_ids)
        remaining = total - watched_count

        if remaining == 0:
            continue  # Fully complete

        last_watched_at = max(e[1] for e in show_watched_entries) if show_watched_entries else None

        remaining_mins = sum(
            ep.runtime_mins or 45
            for s in show.seasons
            for ep in s.episodes
            if ep.id not in watched_ids
        )
        progress_pct = round((watched_count / total) * 100, 1) if total > 0 else 0

        # Find next episode
        next_ep_model = find_next_episode(show, watched_ids)
        
        next_ep_data = None
        if next_ep_model:
            # Find which season this ep belongs to for season_number
            ep_season = next((s for s in show.seasons if s.id == next_ep_model.season_id), None)
            
            next_ep_data = EpisodeResponse(
                id=next_ep_model.id,
                episode_number=next_ep_model.episode_number,
                season_number=ep_season.season_number if ep_season else None,
                name=next_ep_model.name,
                runtime_mins=next_ep_model.runtime_mins,
                air_date=next_ep_model.air_date,
                watched=False,
                watch_history_id=None
            )

        in_progress.append(InProgressShow(
            id=show.id,
            tmdb_id=show.tmdb_id,
            name=show.name,
            poster_path=show.poster_path,
            status=show.status,
            is_dropped=show.is_dropped,
            total_episodes=total,
            watched_episodes=watched_count,
            remaining_episodes=remaining,
            remaining_hours=round(remaining_mins / 60, 1),
            progress_pct=progress_pct,
            next_episode=next_ep_data,
            last_watched_at=last_watched_at
        ))

    # Sort by last_watched_at DESC (most recently watched first)
    return sorted(in_progress, key=lambda s: s.last_watched_at or datetime.min, reverse=True)
