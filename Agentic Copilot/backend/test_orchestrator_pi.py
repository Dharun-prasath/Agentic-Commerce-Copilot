import asyncio
from app.services.orchestrator.service import OrchestratorService
from app.agents.product_intelligence.agent import ProductIntelligenceAgent
import uuid

async def main():
    service = OrchestratorService()
    # Find a valid session_id from DB
    from app.core.database import async_session_maker
    from app.models.models import CustomerSession, OrchestratorJob
    from sqlalchemy import select
    
    async with async_session_maker() as db:
        res = await db.execute(select(CustomerSession).limit(1))
        session = res.scalar_one_or_none()
        if not session:
            print("No session found.")
            return
            
        session_id = session.session_id
        
        # Create a mock job
        job_id = str(uuid.uuid4())
        job = OrchestratorJob(
            id=job_id,
            session_id=session_id,
            agent_type="product",
            status="QUEUED"
        )
        db.add(job)
        await db.commit()
        
    req = {
        "category": "laptop",
        "primary_use": "programming and video editing",
        "budget_max": 200000
    }
    
    # Run the orchestrator trigger
    res = await service._trigger_product_intelligence(job_id, session_id, req)
    print("RESULT:", res)
    
    async with async_session_maker() as db:
        res = await db.execute(select(OrchestratorJob).where(OrchestratorJob.id == job_id))
        job = res.scalar_one_or_none()
        print("JOB STATUS:", job.status)

if __name__ == "__main__":
    asyncio.run(main())
