from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.movie import Movie
from app.models.tv_show import TvShow
from app.models.season import Season
from app.models.watch_history import WatchHistory
from app.schemas.movie import MovieSearchResult
from app.schemas.tv_show import ShowSearchResult, EpisodeResponse
from app.services import tmdb_service, show_service

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/movies", response_model=list[MovieSearchResult])
async def search_movies(
    q: str = Query(..., min_length=1, max_length=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    results = await tmdb_service.search_movies(q)

    # Query library entries to mark in_library and provide library_id
    tmdb_ids = [r["tmdb_id"] for r in results]
    owned_rows = await db.execute(
        select(Movie.tmdb_id, Movie.id).where(Movie.user_id == current_user.id, Movie.tmdb_id.in_(tmdb_ids))
    )
    owned_map: dict[int, int] = {r.tmdb_id: r.id for r in owned_rows}
    
    # Check watch status for movies in library
    watched_labels = {}
    if owned_map:
        watched_result = await db.execute(
            select(Movie.tmdb_id)
            .join(WatchHistory, Movie.id == WatchHistory.movie_id)
            .where(Movie.user_id == current_user.id, Movie.tmdb_id.in_(owned_map.keys()))
        )
        watched_tmdb_ids = {r[0] for r in watched_result}
        for tmdb_id in watched_tmdb_ids:
            watched_labels[tmdb_id] = "Watched"

    return [
        MovieSearchResult(
            **r,
            in_library=r["tmdb_id"] in owned_map,
            library_id=owned_map.get(r["tmdb_id"]),
            status_label=watched_labels.get(r["tmdb_id"])
        )
        for r in results
    ]


@router.get("/shows", response_model=list[ShowSearchResult])
async def search_shows(
    q: str = Query(..., min_length=1, max_length=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    results = await tmdb_service.search_shows(q)

    tmdb_ids = [r["tmdb_id"] for r in results]
    # We need seasons and episodes to find next_episode
    owned_rows = await db.execute(
        select(TvShow)
        .where(TvShow.user_id == current_user.id, TvShow.tmdb_id.in_(tmdb_ids))
        .options(selectinload(TvShow.seasons).selectinload(Season.episodes))
    )
    owned_shows = {s.tmdb_id: s for s in owned_rows.scalars().all()}

    output = []
    for r in results:
        show = owned_shows.get(r["tmdb_id"])
        next_ep_data = None
        status_label = None
        
        if show:
            # Find watched episodes
            all_ep_ids = [ep.id for s in show.seasons for ep in s.episodes]

            today = datetime.now().date()
            aired_ep_ids = {
                ep.id for s in show.seasons for ep in s.episodes 
                if ep.air_date is not None and ep.air_date <= today
            }
            total_aired = len(aired_ep_ids)
            watched_ids = set()

            if total_aired > 0 or len(all_ep_ids) > 0:
                watched_result = await db.execute(
                    select(WatchHistory.episode_id).where(
                        WatchHistory.user_id == current_user.id,
                        WatchHistory.episode_id.in_(all_ep_ids),
                    )
                )
                watched_ids = {row.episode_id for row in watched_result}

                watched_aired_count = len(watched_ids & aired_ep_ids)
                if watched_aired_count == 0:
                    status_label = None
                elif watched_aired_count < total_aired:
                    status_label = "In Progress"
                else:
                    status_label = "Complete"

            next_ep_model = show_service.find_next_episode(show, watched_ids)

            if next_ep_model:
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

        output.append(ShowSearchResult(
            **r,
            in_library=show is not None,
            library_id=show.id if show else None,
            is_dropped=show.is_dropped if show else False,
            next_episode=next_ep_data,
            status_label=status_label
        ))
    
    return output
