from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.core.middleware import SecurityHeadersMiddleware
from app.core.scheduler import scheduler, setup_scheduler
from app.routers import (
    auth_router, search_router, movies_router, shows_router,
    dashboard_router, history_router, admin_router,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: start scheduler. Shutdown: stop scheduler cleanly."""
    setup_scheduler()
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Personal Media Tracker",
        description="Self-hosted movie and TV series tracker",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # ── Middleware ────────────────────────────────────────────────────────────
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "PATCH"],
        allow_headers=["Authorization", "Content-Type"],
    )

    # ── Routers ───────────────────────────────────────────────────────────────
    prefix = "/api"
    app.include_router(auth_router, prefix=prefix)
    app.include_router(search_router, prefix=prefix)
    app.include_router(movies_router, prefix=prefix)
    app.include_router(shows_router, prefix=prefix)
    app.include_router(dashboard_router, prefix=prefix)
    app.include_router(history_router, prefix=prefix)
    app.include_router(admin_router, prefix=prefix)

    # ── Health check ──────────────────────────────────────────────────────────
    @app.get("/api/health", tags=["health"])
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
