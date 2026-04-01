from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.season import Season
from app.schemas.tv_show import ShowAddRequest, ShowResponse, SeasonResponse, EpisodeResponse, InProgressShow
from app.schemas.watch import WatchCreate, WatchHistoryEntry
from app.services import show_service

router = APIRouter(prefix="/shows", tags=["shows"])


@router.post("", response_model=ShowResponse, status_code=status.HTTP_201_CREATED)
async def add_show(
    body: ShowAddRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    show = await show_service.add_show(body.tmdb_id, current_user.id, db)
    # Return minimal response (no watch data yet)
    return ShowResponse(
        id=show.id, tmdb_id=show.tmdb_id, name=show.name, overview=show.overview,
        first_air_date=show.first_air_date, genres=show.genres, status=show.status,
        poster_path=show.poster_path, is_dropped=show.is_dropped, added_at=show.added_at,
    )


@router.get("/in-progress", response_model=list[InProgressShow])
async def get_in_progress(
    include_dropped: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await show_service.get_in_progress(current_user.id, db, include_dropped=include_dropped)


@router.get("/{show_id}", response_model=ShowResponse)
async def get_show(
    show_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await show_service.get_show_with_progress(show_id, current_user.id, db)
    show = result["show"]
    watched_map: dict[int, int] = result["watched_map"]

    seasons_out = []
    total_eps = watched_eps = 0
    remaining_mins = 0

    for s in show.seasons:
        ep_out = []
        s_watched = s_remaining = 0
        s_remaining_mins = 0
        for ep in s.episodes:
            total_eps += 1
            wh_id = watched_map.get(ep.id)
            is_watched = wh_id is not None
            if is_watched:
                watched_eps += 1
                s_watched += 1
            else:
                s_remaining += 1
                s_remaining_mins += ep.runtime_mins or 45
                remaining_mins += ep.runtime_mins or 45
            ep_out.append(EpisodeResponse(
                id=ep.id, episode_number=ep.episode_number, name=ep.name,
                runtime_mins=ep.runtime_mins, air_date=ep.air_date,
                watched=is_watched, watch_history_id=wh_id,
            ))
        seasons_out.append(SeasonResponse(
            id=s.id, season_number=s.season_number, name=s.name,
            episode_count=s.episode_count, air_date=s.air_date,
            watched_count=s_watched, remaining_count=s_remaining,
            remaining_hours=round(s_remaining_mins / 60, 1),
            is_complete=(s_remaining == 0 and len(s.episodes) > 0),
            episodes=ep_out,
        ))

    return ShowResponse(
        id=show.id, tmdb_id=show.tmdb_id, name=show.name, overview=show.overview,
        first_air_date=show.first_air_date, genres=show.genres, status=show.status,
        poster_path=show.poster_path, is_dropped=show.is_dropped, added_at=show.added_at, seasons=seasons_out,
        total_episodes=total_eps, watched_episodes=watched_eps,
        remaining_episodes=total_eps - watched_eps,
        remaining_hours=round(remaining_mins / 60, 1),
    )


@router.post("/{show_id}/drop", response_model=ShowResponse)
async def drop_show(
    show_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    show = await show_service.drop_show(show_id, current_user.id, db)
    return await get_show(show.id, current_user, db)


@router.post("/{show_id}/pickup", response_model=ShowResponse)
async def pickup_show(
    show_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    show = await show_service.pickup_show(show_id, current_user.id, db)
    return await get_show(show.id, current_user, db)


@router.post("/{show_id}/episodes/{episode_id}/watch", response_model=WatchHistoryEntry, status_code=status.HTTP_201_CREATED)
async def mark_episode_watched(
    show_id: int,
    episode_id: int,
    body: WatchCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    entry = await show_service.mark_episode_watched(show_id, episode_id, current_user.id, body, db)
    return WatchHistoryEntry(id=entry.id, watched_at=entry.watched_at, rating=entry.rating, note=entry.note, episode_id=episode_id)


@router.post("/{show_id}/seasons/{season_number}/watch", status_code=status.HTTP_201_CREATED)
async def mark_season_watched(
    show_id: int,
    season_number: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    entries = await show_service.mark_season_watched(show_id, season_number, current_user.id, db)
    return {"marked_watched": len(entries)}


@router.delete("/episodes/watch/{watch_history_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unwatch_episode(
    watch_history_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await show_service.unwatch_episode(watch_history_id, current_user.id, db)

