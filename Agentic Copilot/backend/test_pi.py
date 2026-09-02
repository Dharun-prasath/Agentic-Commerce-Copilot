import asyncio
from app.agents.product_intelligence.agent import ProductIntelligenceAgent

async def main():
    agent = ProductIntelligenceAgent()
    req = {
        "category": "laptop",
        "primary_use": "programming and video editing",
        "budget_max": 200000
    }
    res = await agent.generate_recommendations(req, "test_session_id")
    print(res)

if __name__ == "__main__":
    asyncio.run(main())
