import asyncio
from app.services.orchestrator.service import OrchestratorService
import logging

logging.basicConfig(level=logging.INFO)

async def test():
    o = OrchestratorService()
    res = await o.process_commerce_action(
        "test-orchestrator-full-3ae503", 
        "ADD_TO_CART", 
        {"product_id": "bb362054-bbb4-4381-b483-4fbc9603e801", "quantity": 1}
    )
    print("Result:", res)

asyncio.run(test())
