from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.stats import DashboardStats
from app.schemas.tv_show import InProgressShow
from app.schemas.watch import WatchHistoryEntry
from app.services.stats_service import get_dashboard_stats, get_watch_history
from app.services.show_service import get_in_progress

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=dict)
async def dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stats = await get_dashboard_stats(current_user.id, db)
    recent = await get_watch_history(current_user.id, db, limit=20)
    in_progress = await get_in_progress(current_user.id, db)

    return {
        "stats": stats,
        "recent_activity": recent,
        "in_progress": in_progress[:5],  # Top 5 for dashboard widget
    }
