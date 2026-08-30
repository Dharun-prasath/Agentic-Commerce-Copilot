import asyncio
from app.db.session import AsyncSessionLocal
from app.models.models import Product
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Product.slug, Product.is_active).limit(5))
        for r in result.all():
            print(r)

asyncio.run(main())
