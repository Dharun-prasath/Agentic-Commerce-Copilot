import asyncio
import os
import sys

os.chdir("/Users/pheonix/Documents/Razorpay Buildathon/Agentic-Commerce-Copilot/Agentic Copilot/backend")
sys.path.append("/Users/pheonix/Documents/Razorpay Buildathon/Agentic-Commerce-Copilot/Agentic Copilot/backend")

from app.services.commerce.engine import CommerceEngine
import uuid

async def main():
    engine = CommerceEngine()
    
    # Generate a completely random session ID that DOES NOT EXIST in CustomerSession
    # This will trigger the anonymous fallback logic
    session_id = str(uuid.uuid4())
    product_id = "bb362054-bbb4-4381-b483-4fbc9603e801"
    
    print(f"Testing with ANONYMOUS session {session_id}...")
    result = await engine.add_to_cart(session_id=session_id, product_id=product_id, quantity=1)
    
    import pprint
    print("ANONYMOUS RESULT:")
    pprint.pprint(result)

if __name__ == "__main__":
    asyncio.run(main())
