import asyncio
import os
import sys

os.chdir("/Users/pheonix/Documents/Razorpay Buildathon/Agentic-Commerce-Copilot/Agentic Copilot/backend")
sys.path.append("/Users/pheonix/Documents/Razorpay Buildathon/Agentic-Commerce-Copilot/Agentic Copilot/backend")

from app.services.commerce.engine import CommerceEngine

async def main():
    engine = CommerceEngine()
    
    # We use a fake session_id that we pretend the user is using
    session_id = "test-orchestrator-full-3ae503"
    
    # Dell XPS 16 ID
    product_id = "bb362054-bbb4-4381-b483-4fbc9603e801"
    
    print(f"Adding product {product_id} to cart via CommerceEngine...")
    result = await engine.add_to_cart(session_id=session_id, product_id=product_id, quantity=1)
    
    print("RESULT:")
    import pprint
    pprint.pprint(result)

if __name__ == "__main__":
    asyncio.run(main())
