import asyncio
from app.core.database import async_session_maker
from app.models.models import ExecutionTrace
from sqlalchemy import select
import json

async def main():
    async with async_session_maker() as db:
        res = await db.execute(select(ExecutionTrace).where(ExecutionTrace.component_id == "n_telegram").order_by(ExecutionTrace.start_time.desc()).limit(1))
        traces = res.scalars().all()
        for t in traces:
            print(t.component_id, t.status, getattr(t, 'error_details', None))
            for tc in getattr(t, 'tool_calls', []):
                print(tc.get("tool_name"), tc.get("status"), tc.get("error"))

if __name__ == "__main__":
    asyncio.run(main())
