import os
import sys
import asyncio
import httpx
from duckduckgo_search import DDGS
from itertools import islice
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.seed import HIERARCHY, ACCESSORIES_RAW

IMG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend", "public", "images", "products")
os.makedirs(IMG_DIR, exist_ok=True)

async def download_image(query: str, filename: str):
    filepath = os.path.join(IMG_DIR, filename)
    if os.path.exists(filepath):
        print(f"Skipping {filename}, already exists.")
        return filepath
        
    print(f"Searching for: {query}")
    try:
        with DDGS() as ddgs:
            results = list(islice(ddgs.images(query, safesearch='off', type_image='photo'), 3))
            
            for res in results:
                url = res.get('image')
                if not url: continue
                
                try:
                    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                        response = await client.get(url)
                        response.raise_for_status()
                        
                        # Only accept images
                        content_type = response.headers.get("Content-Type", "")
                        if "image" not in content_type:
                            continue
                            
                        # Save
                        with open(filepath, 'wb') as f:
                            f.write(response.content)
                        print(f"✅ Downloaded {filename}")
                        return filepath
                except Exception as e:
                    print(f"Failed to download {url}: {e}")
                    continue
    except Exception as e:
        print(f"DDGS Error for {query}: {e}")
        
    print(f"❌ Failed to find/download image for {query}")
    return None

async def main():
    tasks = []
    
    # Process Laptops
    for b_name, series_dict in HIERARCHY.items():
        for s_name, model_dict in series_dict.items():
            for m_name, sku_list in model_dict.items():
                for sku_variant in sku_list:
                    parts = [p.strip() for p in sku_variant.split("/")]
                    color = parts[-1] if len(parts) > 0 else ""
                    
                    slug_str = f"{b_name}-{m_name}-{sku_variant}".replace(" ", "-").replace("/", "-").replace('"', '').lower()
                    filename = f"{slug_str}.jpg"
                    
                    # Search query tailored for laptops
                    query = f"{b_name} {m_name} {color} laptop high quality"
                    tasks.append(download_image(query, filename))
                    
    # Process Accessories
    for a_name, c_type, targets in ACCESSORIES_RAW:
        a_slug = a_name.replace(" ", "-").lower()
        filename = f"{a_slug}.jpg"
        query = f"{a_name} product photo high quality"
        tasks.append(download_image(query, filename))
        
    print(f"Downloading {len(tasks)} images...")
    # Run sequentially or with small concurrency to avoid rate limits from DDG
    for i in range(0, len(tasks), 3):
        batch = tasks[i:i+3]
        await asyncio.gather(*batch)
        await asyncio.sleep(1) # rate limit protection

if __name__ == "__main__":
    asyncio.run(main())
