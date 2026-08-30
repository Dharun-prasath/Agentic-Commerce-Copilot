import asyncio
from app.db.session import AsyncSessionLocal
from app.services.wishlist_address_service import WishlistService

async def test():
    async with AsyncSessionLocal() as db:
        service = WishlistService(db)
        # using the user id from logs: 67bc07de-84f0-49d8-ad01-1dbf05699e23
        w = await service.get_wishlist("67bc07de-84f0-49d8-ad01-1dbf05699e23")
        print(w.model_dump())

if __name__ == "__main__":
    asyncio.run(test())
