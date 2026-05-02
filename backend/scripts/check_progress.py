
import asyncio
from sqlalchemy import select, func
from app.database import AsyncSessionLocal
from app.models.tv_show import TvShow
from app.models.season import Season
from app.models.episode import Episode
from app.models.watch_history import WatchHistory

async def check_show_progress(show_id: int):
    async with AsyncSessionLocal() as db:
        show = (await db.execute(
            select(TvShow).where(TvShow.id == show_id)
        )).scalar()
        
        all_eps = (await db.execute(
            select(Episode).join(Season).where(Season.show_id == show_id)
        )).scalars().all()
        all_ep_ids = [ep.id for ep in all_eps]
        
        watched_eps = (await db.execute(
            select(WatchHistory.episode_id)
            .where(WatchHistory.episode_id.in_(all_ep_ids))
        )).scalars().all()
        
        print(f"Show: {show.name}")
        print(f"Total Episodes: {len(all_eps)}")
        print(f"Watched Episodes: {len(watched_eps)}")
        print(f"Remaining: {len(all_eps) - len(watched_eps)}")
        
        if len(all_eps) > 0:
            sample_ep = all_eps[0]
            print(f"Sample Episode: {sample_ep.name} (ID: {sample_ep.id}, Season ID: {sample_ep.season_id})")

if __name__ == "__main__":
    asyncio.run(check_show_progress(1))
