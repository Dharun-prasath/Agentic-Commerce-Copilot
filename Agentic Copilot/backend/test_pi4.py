import asyncio
import json

# Mock telemetry to avoid DB errors
import app.core.telemetry as telemetry
class MockTrace:
    def __init__(self, *args, **kwargs): pass
    async def __aenter__(self): return self
    async def __aexit__(self, *args): pass
    def set_input(self, *args): pass
    def set_output(self, *args): pass
    def set_error(self, *args): pass
    def add_event(self, *args): pass
    def add_tool_call(self, *args): pass
telemetry.trace = MockTrace

from app.agents.product_intelligence.agent import ProductIntelligenceAgent

async def main():
    agent = ProductIntelligenceAgent()
    req = {
        "category": "laptop",
        "primary_use": "programming and video editing",
        "budget_max": 200000
    }
    try:
        res = await agent.generate_recommendations(req, "test_session_id")
        print("RESULT SUCCESS!")
        print(res.model_dump_json(indent=2))
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
