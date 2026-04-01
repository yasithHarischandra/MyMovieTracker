from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.movie import MovieSearchResult
from app.schemas.tv_show import ShowSearchResult
from app.services import tmdb_service
from sqlalchemy import select
from app.models.movie import Movie
from app.models.tv_show import TvShow

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

    return [
        MovieSearchResult(
            **r,
            in_library=r["tmdb_id"] in owned_map,
            library_id=owned_map.get(r["tmdb_id"]),
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
    owned_rows = await db.execute(
        select(TvShow.tmdb_id, TvShow.id, TvShow.is_dropped).where(TvShow.user_id == current_user.id, TvShow.tmdb_id.in_(tmdb_ids))
    )
    owned_info = {r.tmdb_id: (r.id, r.is_dropped) for r in owned_rows}

    return [
        ShowSearchResult(
            **r,
            in_library=r["tmdb_id"] in owned_info,
            library_id=owned_info.get(r["tmdb_id"])[0] if r["tmdb_id"] in owned_info else None,
            is_dropped=owned_info.get(r["tmdb_id"])[1] if r["tmdb_id"] in owned_info else False,
        )
        for r in results
    ]
