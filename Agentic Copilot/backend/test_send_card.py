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
    # Chat ID from the user's config or the screenshot. The bot uses it. I will use the one I found in the past logs if I need, or I can just test against 123456 and let it throw the HTTP error to see if it's a URL issue!
    res = await telegram.send_product_card("5346859702", product)
    print("RES:", res)

if __name__ == "__main__":
    asyncio.run(main())
