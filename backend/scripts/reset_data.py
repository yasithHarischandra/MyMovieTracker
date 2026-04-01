import asyncio
import sys
import os

# Add the backend directory to sys.path so we can import 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import delete
from app.database import AsyncSessionLocal, engine
from app.models.movie import Movie
from app.models.tv_show import TvShow
from app.models.season import Season
from app.models.episode import Episode
from app.models.watch_history import WatchHistory

async def reset_data():
    print("Resetting movie and show data...")
    async with AsyncSessionLocal() as session:
        async with session.begin():
            # Due to foreign key cascades, deleting TvShow and Movie 
            # will clean up Seasons, Episodes, and WatchHistory.
            # We delete them in reverse order of dependency if we want to be safe,
            # but CASCADE on the DB level handles it if we just delete the parents.
            
            print("Deleting Watch History...")
            await session.execute(delete(WatchHistory))
            
            print("Deleting Episodes...")
            await session.execute(delete(Episode))
            
            print("Deleting Seasons...")
            await session.execute(delete(Season))
            
            print("Deleting TV Shows...")
            await session.execute(delete(TvShow))
            
            print("Deleting Movies...")
            await session.execute(delete(Movie))
            
        await session.commit()
    
    # Close the engine
    await engine.dispose()
    print("Data reset complete.")

if __name__ == "__main__":
    asyncio.run(reset_data())
