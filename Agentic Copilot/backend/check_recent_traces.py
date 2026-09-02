import asyncio
from app.core.database import async_session_maker
from app.models.models import ExecutionTrace
from sqlalchemy import select

async def main():
    async with async_session_maker() as db:
        res = await db.execute(select(ExecutionTrace).where(ExecutionTrace.status == "FAILED").order_by(ExecutionTrace.start_time.desc()).limit(10))
        traces = res.scalars().all()
        for t in traces:
            print(t.component_id, t.status, t.error_details, t.start_time)

if __name__ == "__main__":
    asyncio.run(main())
