import asyncio
import os
import sys

# Add backend directory to PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import async_session_maker
from sqlalchemy import text

async def get_products():
    async with async_session_maker() as db:
        res = await db.execute(text("SELECT id, name FROM products LIMIT 5"))
        for row in res.mappings():
            print(f"{row['id']}: {row['name']}")

if __name__ == "__main__":
    asyncio.run(get_products())
