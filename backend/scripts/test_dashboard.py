
import asyncio
import json
from datetime import date, datetime
from app.database import AsyncSessionLocal
from app.services.stats_service import get_dashboard_stats, get_watch_history
from app.services.show_service import get_in_progress

class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        return super().default(obj)

async def test_dashboard_api(user_id: int):
    async with AsyncSessionLocal() as db:
        stats = await get_dashboard_stats(user_id, db)
        recent = await get_watch_history(user_id, db, limit=20)
        in_progress = await get_in_progress(user_id, db)
        
        result = {
            "stats": stats,
            "recent_activity": recent,
            "in_progress": in_progress[:5]
        }
        print(json.dumps(result, indent=2, cls=EnhancedJSONEncoder))

if __name__ == "__main__":
    asyncio.run(test_dashboard_api(1))
