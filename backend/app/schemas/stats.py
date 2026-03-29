from pydantic import BaseModel


class MovieStats(BaseModel):
    movies_watched: int
    movie_hours_watched: float


class SeriesStats(BaseModel):
    episodes_watched: int
    series_hours_watched: float
    in_progress_count: int
    total_episodes_tracked: int
    remaining_episodes: int
    remaining_hours: float
    completion_pct: float


class DashboardStats(BaseModel):
    movies: MovieStats
    series: SeriesStats


class PeriodStats(BaseModel):
    movies_watched: int
    movie_hours: float
    episodes_watched: int
    series_hours: float
    total_hours: float
