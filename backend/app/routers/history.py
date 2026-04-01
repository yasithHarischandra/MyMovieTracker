from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.stats import PeriodStats
from app.schemas.watch import WatchHistoryEntry
from app.services.stats_service import get_watch_history, get_period_stats, clear_watch_history

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=list[WatchHistoryEntry])
async def get_history(
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from_dt = _parse_dt(from_date)
    to_dt = _parse_dt(to_date, end_of_day=True)
    return await get_watch_history(current_user.id, db, limit=limit, offset=offset, from_dt=from_dt, to_dt=to_dt)


@router.get("/stats", response_model=PeriodStats)
async def get_stats(
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from_dt = _parse_dt(from_date) or datetime(2000, 1, 1, tzinfo=timezone.utc)
    to_dt = _parse_dt(to_date, end_of_day=True) or datetime.now(timezone.utc)
    return await get_period_stats(current_user.id, from_dt, to_dt, db)


@router.delete("", status_code=204)
async def clear_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await clear_watch_history(current_user.id, db)
    return None


def _parse_dt(s: Optional[str], end_of_day: bool = False) -> Optional[datetime]:
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        try:
            from datetime import date
            d = date.fromisoformat(s[:10])
            dt = datetime(d.year, d.month, d.day, 23 if end_of_day else 0,
                          59 if end_of_day else 0, 59 if end_of_day else 0,
                          tzinfo=timezone.utc)
        except ValueError:
            return None
    return dt
