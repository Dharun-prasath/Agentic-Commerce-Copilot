import asyncio
from app.db.session import AsyncSessionLocal
from app.models.models import Product
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Product).limit(8))
        products = result.scalars().all()
        for p in products:
            p.is_featured = True
        await session.commit()
        print(f"Set {len(products)} products to featured.")

asyncio.run(main())
