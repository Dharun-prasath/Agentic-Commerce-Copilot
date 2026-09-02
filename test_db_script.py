import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
import json

async def main():
    engine = create_async_engine("postgresql+asyncpg://postgres:postgres@localhost:5432/ecommerce_demo")
    async with engine.connect() as conn:
        from sqlalchemy import text
        res = await conn.execute(text("SELECT id, email FROM users LIMIT 1"))
        user = res.fetchone()
        if user:
            print("USER:", user[0], user[1])
        else:
            print("NO USER FOUND")
            
if __name__ == "__main__":
    asyncio.run(main())
