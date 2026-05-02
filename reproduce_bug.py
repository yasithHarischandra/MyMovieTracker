
import asyncio
import pytest
from unittest.mock import patch, MagicMock
from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import AsyncSessionLocal, Base, engine
from app.models.tv_show import TvShow
from app.models.season import Season
from app.models.episode import Episode
from app.services.sync_service import _sync_one_show

@pytest.mark.asyncio
async def test_reproduce_episode_name_not_updated():
    # Setup: Create a show with an episode that has a generic name
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        show = TvShow(
            tmdb_id=123,
            user_id=1,
            name="The Boys",
            status="Returning Series"
        )
        db.add(show)
        await db.flush()

        season = Season(
            show_id=show.id,
            season_number=4,
            name="Season 4",
            episode_count=1
        )
        db.add(season)
        await db.flush()

        episode = Episode(
            season_id=season.id,
            episode_number=1,
            name="Episode 1",
            runtime_mins=60
        )
        db.add(episode)
        await db.commit()
        show_id = show.id

    # Mock TMDB update with the actual name
    mock_tmdb_data = {
        "tmdb_id": 123,
        "name": "The Boys",
        "status": "Returning Series",
        "seasons": [
            {
                "season_number": 4,
                "name": "Season 4",
                "episode_count": 1,
                "episodes": [
                    {
                        "episode_number": 1,
                        "name": "Department of Dirty Tricks",
                        "runtime_mins": 60,
                        "air_date": "2024-06-13"
                    }
                ]
            }
        ]
    }

    with patch("app.services.tmdb_service.get_show_update", return_value=asyncio.Future()):
        import app.services.tmdb_service as tmdb_service
        tmdb_service.get_show_update = MagicMock(return_value=mock_tmdb_data)
        
        # Run sync
        await _sync_one_show(show_id)

    # Check if name was updated
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Episode).where(Episode.episode_number == 1)
        )
        updated_episode = result.scalar_one()
        print(f"Episode name after sync: {updated_episode.name}")
        
        if updated_episode.name == "Episode 1":
            print("BUG REPRODUCED: Episode name was not updated!")
        else:
            print("SUCCESS: Episode name was updated.")

if __name__ == "__main__":
    asyncio.run(test_reproduce_episode_name_not_updated())
