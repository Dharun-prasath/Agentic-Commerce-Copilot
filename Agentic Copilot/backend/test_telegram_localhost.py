import asyncio
from app.integrations.telegram.provider import RealTelegramProvider

async def main():
    telegram = RealTelegramProvider()
    
    # We will fetch a real chat_id from an event
    from app.core.database import async_session_maker
    from app.models.models import Customer
    from sqlalchemy import select
    chat_id = None
    async with async_session_maker() as db:
        res = await db.execute(select(Customer).where(Customer.telegram_chat_id != None).limit(1))
        c = res.scalar_one_or_none()
        if c: chat_id = c.telegram_chat_id
    
    if not chat_id:
        chat_id = "513361099" # Let's try some dummy ID or maybe fetch it via scratch/get_telegram_chat_id.py that I used before!
        import sys
        sys.path.append("/Users/pheonix/.gemini/antigravity-ide/brain/8bbee1e7-7282-47a8-ba05-0d18595a4602/scratch")
        try:
            from get_telegram_chat_id import get_chat_id
            chat_id = await get_chat_id()
        except:
            pass
            
    print("TESTING WITH CHAT ID:", chat_id)
    
    # Test sending JUST text with URL
    payload = {
        "chat_id": chat_id or "513361099", # Replace with actual if known
        "text": "Test message",
        "parse_mode": "HTML",
        "reply_markup": {
            "inline_keyboard": [
                [{"text": "🛒 View Product", "url": "http://localhost:8001/products/dell-xps"}]
            ]
        }
    }
    import httpx
    url = f"{telegram.api_url}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, json=payload)
            print("RESPONSE:", response.status_code, response.json())
    except Exception as e:
        print("EXCEPTION:", e)

if __name__ == "__main__":
    asyncio.run(main())
