import asyncio
import os
import sys

# Add backend directory to PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import async_session_maker
from sqlalchemy import text

async def reset_db():
    print("Connecting to database to clear intent pipeline data...")
    async with async_session_maker() as db:
        # Tables to clear in order (respecting foreign key dependencies if any)
        tables = [
            "intent_score_history",
            "intent_assessments",
            "intent_agent_jobs",
            "orchestrator_jobs",
            "behavior_events",
            "customer_sessions"
        ]
        
        for table in tables:
            print(f"Clearing {table}...")
            await db.execute(text(f"DELETE FROM {table}"))
        
        await db.commit()
        print("Successfully removed all sessions, events, inputs, and outputs from the database.")

if __name__ == "__main__":
    asyncio.run(reset_db())
