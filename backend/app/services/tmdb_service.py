import asyncio
from typing import Optional
import httpx

from app.config import get_settings

settings = get_settings()

TMDB_BASE = "https://api.themoviedb.org/3"
POSTER_BASE = "https://image.tmdb.org/t/p/w500"
TIMEOUT = 10.0


def _poster_url(path: Optional[str]) -> Optional[str]:
    return f"{POSTER_BASE}{path}" if path else None


async def _get(client: httpx.AsyncClient, endpoint: str, params: dict | None = None) -> dict:
    p = {"api_key": settings.TMDB_API_KEY, **(params or {})}
    resp = await client.get(f"{TMDB_BASE}{endpoint}", params=p, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def _genre_names(genre_list: list[dict]) -> list[str]:
    return [g["name"] for g in genre_list if "name" in g]


async def search_movies(query: str) -> list[dict]:
    async with httpx.AsyncClient() as client:
        data = await _get(client, "/search/movie", {"query": query, "include_adult": "false"})
    results = []
    for r in data.get("results", [])[:20]:
        results.append({
            "tmdb_id": r["id"],
            "title": r.get("title", ""),
            "overview": r.get("overview"),
            "release_date": r.get("release_date"),
            "poster_path": _poster_url(r.get("poster_path")),
            "genres": [],
        })
    return results


async def search_shows(query: str) -> list[dict]:
    async with httpx.AsyncClient() as client:
        data = await _get(client, "/search/tv", {"query": query, "include_adult": "false"})
    results = []
    for r in data.get("results", [])[:20]:
        results.append({
            "tmdb_id": r["id"],
            "name": r.get("name", ""),
            "overview": r.get("overview"),
            "first_air_date": r.get("first_air_date"),
            "poster_path": _poster_url(r.get("poster_path")),
            "genres": [],
            "status": None,
        })
    return results


async def get_movie_detail(tmdb_id: int) -> dict:
    async with httpx.AsyncClient() as client:
        data = await _get(client, f"/movie/{tmdb_id}")
    return {
        "tmdb_id": data["id"],
        "title": data.get("title", ""),
        "overview": data.get("overview"),
        "release_date": data.get("release_date") or None,
        "runtime_mins": data.get("runtime"),
        "genres": ",".join(_genre_names(data.get("genres", []))),
        "poster_path": _poster_url(data.get("poster_path")),
    }


async def get_show_detail(tmdb_id: int) -> dict:
    async with httpx.AsyncClient() as client:
        data = await _get(client, f"/tv/{tmdb_id}")
        # Fetch all seasons in parallel (skip season 0 = specials)
        seasons_raw = [s for s in data.get("seasons", []) if s.get("season_number", 0) > 0]
        season_details = await asyncio.gather(*[
            _get(client, f"/tv/{tmdb_id}/season/{s['season_number']}")
            for s in seasons_raw
        ])

    seasons = []
    for detail in season_details:
        episodes = []
        for ep in detail.get("episodes", []):
            episodes.append({
                "episode_number": ep["episode_number"],
                "name": ep.get("name"),
                "runtime_mins": ep.get("runtime") or 45,  # default 45 if missing
                "air_date": ep.get("air_date") or None,
            })
        seasons.append({
            "season_number": detail["season_number"],
            "name": detail.get("name"),
            "episode_count": len(episodes),
            "air_date": detail.get("air_date") or None,
            "episodes": episodes,
        })

    return {
        "tmdb_id": data["id"],
        "name": data.get("name", ""),
        "overview": data.get("overview"),
        "first_air_date": data.get("first_air_date") or None,
        "genres": ",".join(_genre_names(data.get("genres", []))),
        "status": data.get("status"),
        "poster_path": _poster_url(data.get("poster_path")),
        "seasons": seasons,
    }


async def get_show_update(tmdb_id: int) -> dict:
    """Lightweight update check — returns status and new seasons only."""
    return await get_show_detail(tmdb_id)


def poster_url(path: Optional[str]) -> Optional[str]:
    return _poster_url(path)
