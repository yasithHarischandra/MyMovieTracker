from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ShowAddRequest(BaseModel):
    tmdb_id: int = Field(..., gt=0)


class EpisodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    episode_number: int
    name: Optional[str] = None
    runtime_mins: Optional[int] = None
    air_date: Optional[date] = None
    watched: bool = False
    watch_history_id: Optional[int] = None  # for unwatch


class SeasonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    season_number: int
    name: Optional[str] = None
    episode_count: int
    air_date: Optional[date] = None
    watched_count: int = 0
    remaining_count: int = 0
    remaining_hours: float = 0.0
    is_complete: bool = False
    episodes: list[EpisodeResponse] = []


class ShowBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tmdb_id: int
    name: str
    overview: Optional[str] = None
    first_air_date: Optional[date] = None
    genres: Optional[str] = None
    status: Optional[str] = None
    poster_path: Optional[str] = None
    added_at: datetime


class ShowResponse(ShowBase):
    seasons: list[SeasonResponse] = []
    total_episodes: int = 0
    watched_episodes: int = 0
    remaining_episodes: int = 0
    remaining_hours: float = 0.0


class ShowSearchResult(BaseModel):
    tmdb_id: int
    name: str
    overview: Optional[str] = None
    first_air_date: Optional[str] = None
    genres: Optional[list[str]] = None
    poster_path: Optional[str] = None
    status: Optional[str] = None
    in_library: bool = False
    library_id: Optional[int] = None


class InProgressShow(BaseModel):
    id: int
    tmdb_id: int
    name: str
    poster_path: Optional[str] = None
    status: Optional[str] = None
    total_episodes: int
    watched_episodes: int
    remaining_episodes: int
    remaining_hours: float
    progress_pct: float
