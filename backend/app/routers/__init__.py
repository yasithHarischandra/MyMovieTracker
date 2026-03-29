from app.routers.auth import router as auth_router
from app.routers.search import router as search_router
from app.routers.movies import router as movies_router
from app.routers.shows import router as shows_router
from app.routers.dashboard import router as dashboard_router
from app.routers.history import router as history_router
from app.routers.admin import router as admin_router

__all__ = [
    "auth_router", "search_router", "movies_router", "shows_router",
    "dashboard_router", "history_router", "admin_router",
]
