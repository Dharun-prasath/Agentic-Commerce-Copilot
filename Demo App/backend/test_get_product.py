import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.session import AsyncSessionLocal
from app.services.product_service import ProductService

async def main():
    async with AsyncSessionLocal() as db:
        svc = ProductService(db)
        try:
            p = await svc.get_product("apple-macbook-air-15-m5---16gb---512gb---sky-blue")
            print("Success!", p.name)
        except Exception as e:
            import traceback
            traceback.print_exc()

asyncio.run(main())
