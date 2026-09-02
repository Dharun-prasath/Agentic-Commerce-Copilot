import asyncio
from app.integrations.telegram.provider import RealTelegramProvider

async def main():
    telegram = RealTelegramProvider()
    product = {
      "product_id": "bb362054-bbb4-4381-b483-4fbc9603e801",
      "product_name": "XPS 16 - Core Ultra 9 / 64GB / 2TB",
      "product_slug": "dell-xps-16-core-ultra-9---64gb---2tb",
      "brand": "Dell",
      "product_url": "/products/dell-xps-16-core-ultra-9---64gb---2tb",
      "image_url": "/images/products/dell_xps.png",
      "price": 150000.0,
      "original_price": 170000.0,
      "rating": 4.0,
      "review_count": 45,
      "match_score": 0.8,
      "match_reason": "high performance for development",
      "key_features": [],
      "category": "Laptops"
    }
    
    # Let's bypass the image failure and just test the text message
    telegram._post = custom_post.__get__(telegram)
    
    try:
        await telegram.send_product_card("5346859702", product)
    except Exception as e:
        print(e)

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
