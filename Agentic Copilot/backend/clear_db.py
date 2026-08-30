import asyncio
from app.core.database import async_session_maker
from app.models.models import CustomerSession, BehaviorEvent, IntentScoreHistory, IntentAssessment, IntentAgentJob, AgentExecution

async def clear_db():
    async with async_session_maker() as db:
        await db.execute(IntentAgentJob.__table__.delete())
        await db.execute(IntentAssessment.__table__.delete())
        await db.execute(IntentScoreHistory.__table__.delete())
        await db.execute(BehaviorEvent.__table__.delete())
        await db.execute(CustomerSession.__table__.delete())
        await db.commit()
        print("Database cleared.")

if __name__ == "__main__":
    asyncio.run(clear_db())
