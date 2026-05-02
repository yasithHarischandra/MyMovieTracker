
import asyncio
import logging
from sqlalchemy import select, delete, func, update
from app.database import AsyncSessionLocal, engine
from app.models.tv_show import TvShow
from app.models.season import Season
from app.models.episode import Episode
from app.models.watch_history import WatchHistory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_duplicates():
    async with AsyncSessionLocal() as db:
        # 1. Fix Duplicate Seasons
        # Find (show_id, season_number) pairs with more than 1 entry
        dup_seasons_query = (
            select(Season.show_id, Season.season_number)
            .group_by(Season.show_id, Season.season_number)
            .having(func.count(Season.id) > 1)
        )
        dup_seasons = (await db.execute(dup_seasons_query)).all()
        
        logger.info(f"Found {len(dup_seasons)} duplicate season sets")
        
        for show_id, sn in dup_seasons:
            # Get all IDs for this season, ordered by ID (keep the first one)
            ids_query = (
                select(Season.id)
                .where(Season.show_id == show_id, Season.season_number == sn)
                .order_by(Season.id)
            )
            season_ids = (await db.execute(ids_query)).scalars().all()
            keep_id = season_ids[0]
            redundant_ids = season_ids[1:]
            
            logger.info(f"Merging Season {sn} for Show {show_id}: keeping {keep_id}, removing {redundant_ids}")
            
            # Repoint episodes from redundant seasons to the kept season
            # But wait, episodes might also be duplicated. 
            # It's safer to move episodes, then fix duplicate episodes within the kept season.
            await db.execute(
                update(Episode)
                .where(Episode.season_id.in_(redundant_ids))
                .values(season_id=keep_id)
            )
            
            # Delete redundant seasons
            await db.execute(
                delete(Season).where(Season.id.in_(redundant_ids))
            )
        
        await db.flush()
        
        # 2. Fix Duplicate Episodes
        # Now that all episodes are under the correct seasons, find duplicates within seasons
        dup_episodes_query = (
            select(Episode.season_id, Episode.episode_number)
            .group_by(Episode.season_id, Episode.episode_number)
            .having(func.count(Episode.id) > 1)
        )
        dup_episodes = (await db.execute(dup_episodes_query)).all()
        
        logger.info(f"Found {len(dup_episodes)} duplicate episode sets")
        
        for season_id, en in dup_episodes:
            ids_query = (
                select(Episode.id)
                .where(Episode.season_id == season_id, Episode.episode_number == en)
                .order_by(Episode.id)
            )
            ep_ids = (await db.execute(ids_query)).scalars().all()
            keep_id = ep_ids[0]
            redundant_ids = ep_ids[1:]
            
            logger.info(f"Merging Episode {en} for Season {season_id}: keeping {keep_id}, removing {redundant_ids}")
            
            # Repoint watch history
            await db.execute(
                update(WatchHistory)
                .where(WatchHistory.episode_id.in_(redundant_ids))
                .values(episode_id=keep_id)
            )
            
            # Delete redundant episodes
            await db.execute(
                delete(Episode).where(Episode.id.in_(redundant_ids))
            )
            
        await db.commit()
        logger.info("Data correction complete.")

if __name__ == "__main__":
    asyncio.run(fix_duplicates())
