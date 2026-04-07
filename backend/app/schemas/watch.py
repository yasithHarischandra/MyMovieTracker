from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, field_serializer


class WatchCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    rating: Optional[int] = Field(None, ge=1, le=5)
    note: Optional[str] = Field(None, max_length=500)

    @field_validator("note")
    @classmethod
    def sanitize_note(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            # Strip to plain text — prevent stored XSS via note field
            v = v.strip()
            return v if v else None
        return v


class WatchHistoryEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    watched_at: datetime
    rating: Optional[int] = None

    @field_serializer("watched_at")
    def serialize_watched_at(self, v: datetime) -> str:
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v.isoformat().replace("+00:00", "Z")
    note: Optional[str] = None

    # Movie fields (populated when this is a movie watch)
    movie_id: Optional[int] = None
    movie_title: Optional[str] = None
    movie_poster_path: Optional[str] = None
    movie_runtime_mins: Optional[int] = None

    # Episode fields (populated when this is an episode watch)
    episode_id: Optional[int] = None
    show_id: Optional[int] = None
    show_name: Optional[str] = None
    show_poster_path: Optional[str] = None
    season_number: Optional[int] = None
    episode_number: Optional[int] = None
    episode_name: Optional[str] = None
    episode_runtime_mins: Optional[int] = None

    @property
    def media_type(self) -> str:
        return "movie" if self.movie_id else "episode"
