from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class MovieAddRequest(BaseModel):
    tmdb_id: int = Field(..., gt=0)


class MovieBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tmdb_id: int
    title: str
    overview: Optional[str] = None
    release_date: Optional[date] = None
    runtime_mins: Optional[int] = None
    genres: Optional[str] = None
    poster_path: Optional[str] = None
    added_at: datetime


class MovieResponse(MovieBase):
    watch_count: int = 0


class MovieSearchResult(BaseModel):
    tmdb_id: int
    title: str
    overview: Optional[str] = None
    release_date: Optional[str] = None
    runtime_mins: Optional[int] = None
    genres: Optional[list[str]] = None
    poster_path: Optional[str] = None
    in_library: bool = False
    library_id: Optional[int] = None
    status_label: Optional[str] = None
