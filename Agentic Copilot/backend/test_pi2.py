import asyncio
from app.agents.product_intelligence.agent import ProductIntelligenceAgent
from app.core.telemetry import trace

async def main():
    agent = ProductIntelligenceAgent()
    req = {
        "category": "laptop",
        "primary_use": "programming and video editing",
        "budget_max": 200000
    }
    # Use the session_id from the logs that we saw failing earlier
    res = await agent.generate_recommendations(req, "test_session_id")
    print("RESULT:", res)

if __name__ == "__main__":
    asyncio.run(main())
