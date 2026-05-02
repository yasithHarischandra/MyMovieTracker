
import asyncio
from sqlalchemy import select, func
from app.database import AsyncSessionLocal
from app.models.tv_show import TvShow
from app.models.season import Season
from app.models.episode import Episode
from app.models.watch_history import WatchHistory

async def check_db():
    async with AsyncSessionLocal() as db:
        show_count = (await db.execute(select(func.count(TvShow.id)))).scalar()
        season_count = (await db.execute(select(func.count(Season.id)))).scalar()
        episode_count = (await db.execute(select(func.count(Episode.id)))).scalar()
        history_count = (await db.execute(select(func.count(WatchHistory.id)).where(WatchHistory.episode_id.isnot(None)))).scalar()
        
        print(f"TV Shows: {show_count}")
        print(f"Seasons: {season_count}")
        print(f"Episodes: {episode_count}")
        print(f"Watch History (Episodes): {history_count}")
        
        if show_count > 0:
            sample_show = (await db.execute(select(TvShow).limit(1))).scalar()
            print(f"Sample Show: {sample_show.name} (ID: {sample_show.id}, User ID: {sample_show.user_id})")
            
            # Check seasons for this show
            s_count = (await db.execute(select(func.count(Season.id)).where(Season.show_id == sample_show.id))).scalar()
            print(f"Seasons for sample show: {s_count}")

if __name__ == "__main__":
    asyncio.run(check_db())
