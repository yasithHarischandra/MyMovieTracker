from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.exc import IntegrityError
from datetime import date as date_type

from app.models.movie import Movie
from app.models.watch_history import WatchHistory
from app.schemas.watch import WatchCreate
from app.schemas.movie import MovieResponse
from app.services import tmdb_service


async def add_movie(tmdb_id: int, user_id: int, db: AsyncSession) -> Movie:
    # Check if already in library
    result = await db.execute(
        select(Movie).where(Movie.tmdb_id == tmdb_id, Movie.user_id == user_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Movie already in library")

    # Fetch from TMDB
    try:
        data = await tmdb_service.get_movie_detail(tmdb_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to fetch movie from TMDB")

    # Parse release_date safely
    rd = data.get("release_date")
    if isinstance(rd, str) and rd:
        try:
            rd = date_type.fromisoformat(rd)
        except ValueError:
            rd = None

    movie = Movie(
        tmdb_id=data["tmdb_id"],
        user_id=user_id,
        title=data["title"],
        overview=data.get("overview"),
        release_date=rd,
        runtime_mins=data.get("runtime_mins"),
        genres=data.get("genres"),
        poster_path=data.get("poster_path"),
    )
    db.add(movie)
    try:
        await db.commit()
        await db.refresh(movie)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Movie already in library")
    return movie


async def get_movie(movie_id: int, user_id: int, db: AsyncSession) -> Movie:
    result = await db.execute(
        select(Movie).where(Movie.id == movie_id, Movie.user_id == user_id)
    )
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found")
    return movie


async def mark_watched(movie_id: int, user_id: int, watch_data: WatchCreate, db: AsyncSession) -> WatchHistory:
    movie = await get_movie(movie_id, user_id, db)
    entry = WatchHistory(
        user_id=user_id,
        movie_id=movie.id,
        rating=watch_data.rating,
        note=watch_data.note,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def unwatch(watch_history_id: int, user_id: int, db: AsyncSession) -> None:
    result = await db.execute(
        select(WatchHistory).where(
            WatchHistory.id == watch_history_id,
            WatchHistory.user_id == user_id,
            WatchHistory.movie_id.isnot(None),
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watch history entry not found")
    await db.delete(entry)
    await db.commit()


async def get_movie_watch_history(movie_id: int, user_id: int, db: AsyncSession) -> list[WatchHistory]:
    result = await db.execute(
        select(WatchHistory)
        .where(WatchHistory.movie_id == movie_id, WatchHistory.user_id == user_id)
        .order_by(WatchHistory.watched_at.desc())
    )
    return list(result.scalars().all())
