import json
import logging
from datetime import datetime, timezone, date as date_type
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.movie import Movie
from app.models.tv_show import TvShow
from app.models.season import Season
from app.models.episode import Episode
from app.models.watch_history import WatchHistory
from app.services import tmdb_service

logger = logging.getLogger(__name__)


def _parse_date(s: Optional[str]) -> Optional[date_type]:
    if isinstance(s, str) and s:
        try:
            return date_type.fromisoformat(s[:10])
        except ValueError:
            return None
    return None


def _parse_dt(s: Optional[str]) -> Optional[datetime]:
    if isinstance(s, str) and s:
        for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
            try:
                return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
    return datetime.now(timezone.utc)


async def import_trakt_json(raw: bytes, user_id: int, db: AsyncSession) -> dict:
    """
    Parse a Trakt.tv JSON export and import movies + episodes.
    Expected format: {"movies": [...], "episodes": [...]}
    Each movie: {"movie": {"ids": {"tmdb": int}}, "watched_at": str}
    Each episode: {"show": {"ids": {"tmdb": int}}, "episode": {"season": int, "number": int}, "watched_at": str}
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON file"}

    movies_data = data.get("movies", [])
    episodes_data = data.get("episodes", [])

    imported_movies = 0
    imported_episodes = 0
    skipped = 0

    # ── Import movies ──────────────────────────────────────────────────────
    for entry in movies_data:
        tmdb_id = entry.get("movie", {}).get("ids", {}).get("tmdb")
        watched_at = _parse_dt(entry.get("watched_at"))
        if not tmdb_id:
            skipped += 1
            continue

        # Upsert movie
        movie_result = await db.execute(
            select(Movie).where(Movie.tmdb_id == tmdb_id, Movie.user_id == user_id)
        )
        movie = movie_result.scalar_one_or_none()
        if not movie:
            try:
                detail = await tmdb_service.get_movie_detail(tmdb_id)
                movie = Movie(
                    tmdb_id=detail["tmdb_id"],
                    user_id=user_id,
                    title=detail["title"],
                    overview=detail.get("overview"),
                    release_date=_parse_date(detail.get("release_date")),
                    runtime_mins=detail.get("runtime_mins"),
                    genres=detail.get("genres"),
                    poster_path=detail.get("poster_path"),
                )
                db.add(movie)
                await db.flush()
            except Exception as exc:
                logger.warning(f"Trakt import: failed to fetch movie tmdb_id={tmdb_id}: {exc}")
                skipped += 1
                continue

        wh = WatchHistory(user_id=user_id, movie_id=movie.id, watched_at=watched_at)
        db.add(wh)
        imported_movies += 1

    # ── Import episodes ────────────────────────────────────────────────────
    # Group by show tmdb_id first to minimise TMDB API calls
    show_map: dict[int, dict] = {}
    for entry in episodes_data:
        tmdb_id = entry.get("show", {}).get("ids", {}).get("tmdb")
        if not tmdb_id:
            skipped += 1
            continue
        show_map.setdefault(tmdb_id, {"entries": []})["entries"].append(entry)

    for show_tmdb_id, payload in show_map.items():
        show_result = await db.execute(
            select(TvShow).where(TvShow.tmdb_id == show_tmdb_id, TvShow.user_id == user_id)
        )
        show = show_result.scalar_one_or_none()

        if not show:
            try:
                detail = await tmdb_service.get_show_detail(show_tmdb_id)
                show = TvShow(
                    tmdb_id=detail["tmdb_id"],
                    user_id=user_id,
                    name=detail["name"],
                    overview=detail.get("overview"),
                    first_air_date=_parse_date(detail.get("first_air_date")),
                    genres=detail.get("genres"),
                    status=detail.get("status"),
                    poster_path=detail.get("poster_path"),
                )
                db.add(show)
                await db.flush()

                for s_data in detail.get("seasons", []):
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
                        db.add(Episode(
                            season_id=season.id,
                            episode_number=ep["episode_number"],
                            name=ep.get("name"),
                            runtime_mins=ep.get("runtime_mins", 45),
                            air_date=_parse_date(ep.get("air_date")),
                        ))
                await db.flush()
            except Exception as exc:
                logger.warning(f"Trakt import: failed show tmdb_id={show_tmdb_id}: {exc}")
                skipped += len(payload["entries"])
                continue

        # Map episode (season#, ep#) → episode id
        ep_result = await db.execute(
            select(Episode.id, Episode.episode_number, Season.season_number)
            .join(Season, Season.id == Episode.season_id)
            .join(TvShow, TvShow.id == Season.show_id)
            .where(TvShow.id == show.id)
        )
        ep_map = {(row.season_number, row.episode_number): row.id for row in ep_result}

        for entry in payload["entries"]:
            s = entry.get("episode", {}).get("season")
            n = entry.get("episode", {}).get("number")
            watched_at = _parse_dt(entry.get("watched_at"))
            ep_id = ep_map.get((s, n))
            if not ep_id:
                skipped += 1
                continue
            db.add(WatchHistory(user_id=user_id, episode_id=ep_id, watched_at=watched_at))
            imported_episodes += 1

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        return {"error": "Database error during import. Some entries may have been skipped."}

    return {
        "imported_movies": imported_movies,
        "imported_episodes": imported_episodes,
        "skipped": skipped,
    }
