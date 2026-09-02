import asyncio
from app.integrations.telegram.provider import RealTelegramProvider

async def main():
    telegram = RealTelegramProvider()
    
    # We will fetch the user's chat_id from the DB so we don't get "chat not found"
    from app.core.database import async_session_maker
    from app.models.models import CustomerSession
    from sqlalchemy import select
    chat_id = None
    async with async_session_maker() as db:
        res = await db.execute(select(CustomerSession).where(CustomerSession.telegram_chat_id != None).order_by(CustomerSession.created_at.desc()).limit(1))
        s = res.scalar_one_or_none()
        if s: chat_id = s.telegram_chat_id
    
    if not chat_id:
        print("NO CHAT ID FOUND")
        return
        
    print("TESTING WITH CHAT ID:", chat_id)
    
    # Test sending JUST text with URL
    payload = {
        "chat_id": chat_id,
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
