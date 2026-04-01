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

import httpx
from sqlalchemy.exc import IntegrityError, OperationalError

logger = logging.getLogger(__name__)

# Also set up a custom file logger specifically for importing to ensure the user can troubleshoot
import_handler = logging.FileHandler("import_process.log", encoding="utf-8")
import_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(import_handler)
logger.setLevel(logging.INFO)


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
    Supports both legacy dict format and new array formats from Trakt exports.
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error(f"JSON Decode Error: {exc}")
        return {"error": "Invalid JSON file"}
    except Exception as exc:
        logger.exception("Unexpected error parsing initial file upload")
        return {"error": "Unexpected error parsing file upload"}

    movies_data = []
    episodes_data = []

    if isinstance(data, dict):
        movies_data = data.get("movies", [])
        episodes_data = data.get("episodes", [])
    elif isinstance(data, list):
        for entry in data:
            if "movie" in entry:
                if "last_watched_at" in entry and "watched_at" not in entry:
                    entry["watched_at"] = entry["last_watched_at"]
                movies_data.append(entry)
            elif "show" in entry:
                show_data = entry["show"]
                for season in entry.get("seasons", []):
                    s_num = season.get("number")
                    for ep in season.get("episodes", []):
                        e_num = ep.get("number")
                        watched_at = ep.get("last_watched_at") or ep.get("watched_at")
                        episodes_data.append({
                            "show": show_data,
                            "episode": {"season": s_num, "number": e_num},
                            "watched_at": watched_at
                        })

    imported_movies = 0
    imported_episodes = 0
    skipped_items = []

    # ── Import movies ──────────────────────────────────────────────────────
    for entry in movies_data:
        tmdb_id = entry.get("movie", {}).get("ids", {}).get("tmdb")
        watched_at = _parse_dt(entry.get("watched_at"))
        if not tmdb_id:
            title = entry.get("movie", {}).get("title", "Unknown")
            skipped_items.append({"title": title, "reason": "Missing TMDB ID"})
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
                await db.rollback()
                logger.warning(f"Trakt import: failed to fetch movie tmdb_id={tmdb_id}: {exc}")
                title = entry.get("movie", {}).get("title", "Unknown")
                skipped_items.append({"title": title, "reason": f"TMDB Fetch Failed: {exc}"})
                continue

        # Clear existing history for this movie before re-importing to avoid duplicates
        from sqlalchemy import delete
        await db.execute(
            delete(WatchHistory).where(
                WatchHistory.user_id == user_id,
                WatchHistory.movie_id == movie.id
            )
        )

        wh = WatchHistory(user_id=user_id, movie_id=movie.id, watched_at=watched_at)
        db.add(wh)
        imported_movies += 1
        
        try:
            await db.commit()
            logger.info(f"Successfully processed movie: {movie.title}")
        except Exception as exc:
            await db.rollback()
            logger.error(f"Error commiting movie {movie.title}: {exc}")
            skipped_items.append({"title": movie.title, "reason": "Database Commit Error"})

    # ── Import episodes ────────────────────────────────────────────────────
    # Group by show tmdb_id first to minimise TMDB API calls
    show_map: dict[int, dict] = {}
    for entry in episodes_data:
        tmdb_id = entry.get("show", {}).get("ids", {}).get("tmdb")
        if not tmdb_id:
            title = entry.get("show", {}).get("title", "Unknown")
            skipped_items.append({"title": title, "reason": "Missing TMDB ID"})
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
                new_tmdb_id = detail["tmdb_id"]
                
                # Double check with the potentially "normalized" TMDB ID
                if new_tmdb_id != show_tmdb_id:
                    show_result = await db.execute(
                        select(TvShow).where(TvShow.tmdb_id == new_tmdb_id, TvShow.user_id == user_id)
                    )
                    show = show_result.scalar_one_or_none()
                
                if not show:
                    show = TvShow(
                        tmdb_id=new_tmdb_id,
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
                await db.rollback()
                logger.warning(f"Trakt import: failed show tmdb_id={show_tmdb_id}: {exc}")
                title = payload.get("entries", [{}])[0].get("show", {}).get("title", "Unknown") if payload.get("entries") else str(show_tmdb_id)
                skipped_items.append({"title": title, "reason": f"TMDB Fetch/Insert Failed: {exc}"})
                continue

        # Map episode (season#, ep#) → episode id
        ep_result = await db.execute(
            select(Episode.id, Episode.episode_number, Season.season_number)
            .join(Season, Season.id == Episode.season_id)
            .join(TvShow, TvShow.id == Season.show_id)
            .where(TvShow.id == show.id)
        )
        ep_map = {(row.season_number, row.episode_number): row.id for row in ep_result}

        # Clear existing history for this show before re-importing to avoid duplicates
        from sqlalchemy import delete
        await db.execute(
            delete(WatchHistory).where(
                WatchHistory.user_id == user_id,
                WatchHistory.episode_id.in_(list(ep_map.values()))
            )
        )

        for entry in payload["entries"]:
            s = entry.get("episode", {}).get("season")
            n = entry.get("episode", {}).get("number")
            watched_at = _parse_dt(entry.get("watched_at"))
            ep_id = ep_map.get((s, n))
            if not ep_id:
                title = entry.get("show", {}).get("title", "Unknown")
                skipped_items.append({"title": title, "reason": f"Episode Mapping Failed for S{s}E{n}"})
                continue
            db.add(WatchHistory(user_id=user_id, episode_id=ep_id, watched_at=watched_at))
            imported_episodes += 1

        try:
            await db.commit()
            logger.info(f"Successfully processed show: {show.name if show else show_map}")
        except Exception as exc:
            await db.rollback()
            logger.error(f"Error commiting show {show.name if show else show_map}: {exc}")
            skipped_items.append({"title": show.name if show else "Show", "reason": "Database Commit Error"})


    logger.info(f"Import complete! Movies: {imported_movies}, Episodes: {imported_episodes}, Skipped: {len(skipped_items)}")

    return {
        "imported_movies": imported_movies,
        "imported_episodes": imported_episodes,
        "skipped": skipped_items,
    }
