from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.movie import MovieAddRequest, MovieBase
from app.schemas.watch import WatchCreate, WatchHistoryEntry
from app.services import movie_service

router = APIRouter(prefix="/movies", tags=["movies"])


@router.post("", response_model=MovieBase, status_code=status.HTTP_201_CREATED)
async def add_movie(
    body: MovieAddRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await movie_service.add_movie(body.tmdb_id, current_user.id, db)


@router.get("/{movie_id}", response_model=MovieBase)
async def get_movie(
    movie_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await movie_service.get_movie(movie_id, current_user.id, db)


@router.post("/{movie_id}/watch", response_model=WatchHistoryEntry, status_code=status.HTTP_201_CREATED)
async def mark_watched(
    movie_id: int,
    body: WatchCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    entry = await movie_service.mark_watched(movie_id, current_user.id, body, db)
    movie = await movie_service.get_movie(movie_id, current_user.id, db)
    return WatchHistoryEntry(
        id=entry.id,
        watched_at=entry.watched_at,
        rating=entry.rating,
        note=entry.note,
        movie_id=movie.id,
        movie_title=movie.title,
        movie_poster_path=movie.poster_path,
        movie_runtime_mins=movie.runtime_mins,
    )


@router.delete("/watch/{watch_history_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unwatch(
    watch_history_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await movie_service.unwatch(watch_history_id, current_user.id, db)


@router.get("/{movie_id}/history", response_model=list[WatchHistoryEntry])
async def get_movie_history(
    movie_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    movie = await movie_service.get_movie(movie_id, current_user.id, db)
    entries = await movie_service.get_movie_watch_history(movie_id, current_user.id, db)
    return [
        WatchHistoryEntry(
            id=e.id,
            watched_at=e.watched_at,
            rating=e.rating,
            note=e.note,
            movie_id=movie.id,
            movie_title=movie.title,
            movie_poster_path=movie.poster_path,
            movie_runtime_mins=movie.runtime_mins,
        )
        for e in entries
    ]
