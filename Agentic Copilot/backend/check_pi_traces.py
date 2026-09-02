import asyncio
from app.core.database import async_session_maker
from app.models.models import ExecutionTrace
from sqlalchemy import select

async def main():
    async with async_session_maker() as db:
        res = await db.execute(select(ExecutionTrace).where(ExecutionTrace.component_id == "n_product_intelligence").order_by(ExecutionTrace.start_time.desc()).limit(1))
        traces = res.scalars().all()
        for t in traces:
            print(t.component_id, t.status, getattr(t, 'error_details', None), t.outputs)

if __name__ == "__main__":
    asyncio.run(main())
