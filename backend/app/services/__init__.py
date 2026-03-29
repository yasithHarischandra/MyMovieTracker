from app.services.auth_service import authenticate_user, issue_token
from app.services.tmdb_service import search_movies, search_shows, get_movie_detail, get_show_detail
from app.services.movie_service import add_movie, get_movie, mark_watched, unwatch, get_movie_watch_history
from app.services.show_service import add_show, get_show_with_progress, mark_episode_watched, mark_season_watched, unwatch_episode, get_in_progress
from app.services.stats_service import get_dashboard_stats, get_period_stats, get_watch_history
from app.services.sync_service import sync_returning_shows
from app.services.import_service import import_trakt_json

__all__ = [
    "authenticate_user", "issue_token",
    "search_movies", "search_shows", "get_movie_detail", "get_show_detail",
    "add_movie", "get_movie", "mark_watched", "unwatch", "get_movie_watch_history",
    "add_show", "get_show_with_progress", "mark_episode_watched", "mark_season_watched",
    "unwatch_episode", "get_in_progress",
    "get_dashboard_stats", "get_period_stats", "get_watch_history",
    "sync_returning_shows", "import_trakt_json",
]
