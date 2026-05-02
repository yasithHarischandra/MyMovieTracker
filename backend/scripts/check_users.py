
import asyncio
from sqlalchemy import select, func
from app.database import AsyncSessionLocal
from app.models.tv_show import TvShow

async def check_users():
    async with AsyncSessionLocal() as db:
        r = await db.execute(select(TvShow.user_id).distinct())
        print(f"User IDs in library: {r.scalars().all()}")

if __name__ == "__main__":
    asyncio.run(check_users())
