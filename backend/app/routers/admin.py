from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.sync_service import sync_returning_shows
from app.services.import_service import import_trakt_json
from app.services.stats_service import clear_library

router = APIRouter(prefix="/admin", tags=["admin"])

MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB


@router.post("/sync")
async def trigger_sync(current_user: User = Depends(get_current_user)):
    """Manually trigger TMDB returning series sync."""
    result = await sync_returning_shows()
    return result


@router.post("/import/trakt")
async def import_trakt(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a Trakt.tv JSON export to import watch history."""
    if file.content_type not in ("application/json", "text/plain"):
        return {"error": "File must be JSON"}

    raw = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(raw) > MAX_UPLOAD_BYTES:
        return {"error": "File too large (max 50 MB)"}

    return await import_trakt_json(raw, current_user.id, db)


@router.delete("/library", status_code=204)
async def delete_library(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Permanently delete all movies and TV shows for the current user."""
    await clear_library(current_user.id, db)
    return None
