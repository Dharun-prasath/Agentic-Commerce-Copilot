import asyncio
from app.integrations.telegram.provider import RealTelegramProvider

async def main():
    telegram = RealTelegramProvider()
    chat_id = "2019487070"
    
    # Test 1: Just the localhost URL
    payload_url = {
        "chat_id": chat_id,
        "text": "Test localhost URL",
        "parse_mode": "HTML",
        "reply_markup": {
            "inline_keyboard": [
                [{"text": "🛒 View Product", "url": "http://localhost:8001/products/dell-xps"}]
            ]
        }
    }
    
    # Test 2: The full HTML card to check for parse errors
    product = {
      "product_id": "bb362054-bbb4-4381-b483-4fbc9603e801",
      "product_name": "MacBook Pro 16\" - M5 Pro / 24GB / 1TB / Space Black",
      "product_slug": "apple-macbook-pro-16-m5-pro---24gb---1tb---space-black",
      "brand": "Apple",
      "product_url": "/products/apple-macbook",
      "image_url": "/images/products/dell_xps.png",
      "price": 150000.0,
      "original_price": 170000.0,
      "rating": 4.0,
      "review_count": 45,
      "match_score": 0.8,
      "match_reason": "high performance for development, primary use: programming and AI/ML development, category: laptop, budget_max: 200000",
      "key_features": ["test < feature >"],
      "category": "Laptops"
    }
    
    import httpx
    url = f"{telegram.api_url}/sendMessage"
    
    print("--- TEST 1: URL ---")
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(url, json=payload_url)
        print("RESPONSE:", response.status_code, response.json())
        
    print("\n--- TEST 2: HTML ---")
    telegram._post = custom_post.__get__(telegram)
    try:
        await telegram.send_product_card(chat_id, product)
    except Exception as e:
        print("EXCEPTION:", e)

async def custom_post(self, endpoint, payload):
    import httpx
    url = f"{self.api_url}/{endpoint}"
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(url, json=payload)
        print("TELEGRAM RESPONSE:", response.json())
        response.raise_for_status()
        return True

if __name__ == "__main__":
    asyncio.run(main())
