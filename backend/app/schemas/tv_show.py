from datetime import date, datetime, timezone
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_serializer


class ShowAddRequest(BaseModel):
    tmdb_id: int = Field(..., gt=0)


class EpisodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    episode_number: int
    season_number: Optional[int] = None
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
    is_dropped: bool = False
    added_at: datetime


class ShowResponse(ShowBase):
    seasons: list[SeasonResponse] = []
    total_episodes: int = 0
    watched_episodes: int = 0
    remaining_episodes: int = 0
    remaining_hours: float = 0.0
    next_episode: Optional[EpisodeResponse] = None


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
    is_dropped: bool = False
    next_episode: Optional[EpisodeResponse] = None
    status_label: Optional[str] = None


class InProgressShow(BaseModel):
    id: int
    tmdb_id: int
    name: str
    poster_path: Optional[str] = None
    status: Optional[str] = None
    is_dropped: bool = False
    total_episodes: int
    watched_episodes: int
    remaining_episodes: int
    remaining_hours: float
    progress_pct: float
    next_episode: Optional[EpisodeResponse] = None
    last_watched_at: Optional[datetime] = None

    @field_serializer("last_watched_at")
    def serialize_last_watched_at(self, v: Optional[datetime]) -> Optional[str]:
        if v is None:
            return None
        # Ensure it has Z suffix and is treated as UTC
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v.isoformat().replace("+00:00", "Z")


class UpcomingEpisodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    show_id: int
    show_name: str
    show_poster_path: Optional[str] = None
    episode_id: int
    season_number: int
    episode_number: int
    episode_name: Optional[str] = None
    air_date: date
    runtime_mins: Optional[int] = None
    is_dropped: bool = False
