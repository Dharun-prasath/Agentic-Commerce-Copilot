import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

async def check():
    engine = create_async_engine(settings.COPILOT_DATABASE_URL)
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT id, name, telegram_chat_id FROM customers"))
        print("Customers:")
        for r in res.fetchall():
            print(dict(r._mapping))
        
        res = await conn.execute(text("SELECT session_id, user_id FROM customer_sessions"))
        print("\nSessions:")
        for r in res.fetchall():
            print(dict(r._mapping))

asyncio.run(check())
