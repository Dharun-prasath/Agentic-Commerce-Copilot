import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine("postgresql+asyncpg://postgres:password@localhost:5432/agentic_commerce")
    async with engine.connect() as conn:
        print("--- USERS ---")
        res = await conn.execute(text("SELECT id, email FROM users LIMIT 5"))
        for row in res:
            print(row)
            
        print("--- CARTS ---")
        res = await conn.execute(text("SELECT id, user_id, session_id FROM carts ORDER BY created_at DESC LIMIT 5"))
        for row in res:
            print(row)
            
if __name__ == "__main__":
    asyncio.run(main())
