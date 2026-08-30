import asyncio
from app.core.database import async_session_maker
from app.models.models import CustomerSession
from sqlalchemy.future import select

async def main():
    async with async_session_maker() as db:
        res = await db.execute(select(CustomerSession))
        for s in res.scalars():
            print(f"session_id={s.session_id}, status={s.status}, threshold_reached={s.threshold_reached}")

if __name__ == "__main__":
    asyncio.run(main())
