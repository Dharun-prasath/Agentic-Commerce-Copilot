import asyncio
from app.db.session import AsyncSessionLocal
from app.schemas.auth import UserRegister
from app.services.auth_service import AuthService

async def main():
    async with AsyncSessionLocal() as db:
        try:
            service = AuthService(db)
            data = UserRegister(
                email="test4@example.com",
                password="password123",
                name="Test"
            )
            res = await service.register(data)
            await db.commit()
            print("Success:", res)
        except Exception as e:
            print("ERROR:")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
