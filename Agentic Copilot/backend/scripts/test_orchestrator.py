import asyncio
import os
import sys

# Add backend dir to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.orchestrator.service import OrchestratorService
from app.models.models import CustomerSession
from app.core.database import async_session_maker
from datetime import datetime
import uuid
import logging

logging.basicConfig(level=logging.INFO)

async def test_full_orchestration():
    print("Testing Production-Ready Multi-Agent Orchestration Integration...")
    
    # 1. Create a fake session ID
    session_id = f"test-orchestrator-{str(uuid.uuid4())[:8]}"
    print(f"\n[1] Starting orchestration for session {session_id}")
    
    async with async_session_maker() as db:
        from app.models.models import Customer, CustomerSession
        customer = Customer(
            id=str(uuid.uuid4()),
            telegram_chat_id="2019487070"
        )
        db.add(customer)
        await db.commit()
        
        session = CustomerSession(
            session_id=session_id, 
            user_id=customer.id,
            last_active=datetime.utcnow().isoformat() + "Z"
        )
        db.add(session)
        await db.commit()
    
    
    # 2. Simulate Intent Output
    print("\n[2] Simulating Intent Output...")
    intent_output = {
        "intent_category": "Consideration",
        "confidence": 0.95,
        "customer_interest": "Looking for a high performance laptop for gaming",
        "behaviour_summary": "User searched for 'gaming laptop' and looked at Dell and ASUS models.",
        "products_of_interest": [],
        "categories_of_interest": ["Laptops"],
        "reasoning": "User explicitly stated interest in gaming laptops.",
        "recommended_action": "PROCEED",
        "sales_consultant_context": "User is a gamer looking for a high-performance machine."
    }
    
    # 3. Initialize Orchestrator
    orchestrator = OrchestratorService()
    
    # 4. Process Intent Output (This triggers Product Intelligence async)
    print("\n[3] Orchestrator processing intent output...")
    await orchestrator.process_intent_output(session_id, intent_output)
    
    print("\n[4] Waiting for background Product Intelligence task to complete (up to 60s)...")
    
    from app.models.models import OrchestratorJob
    from sqlalchemy.future import select
    
    max_wait = 120
    job_status = "UNKNOWN"
    for i in range(max_wait):
        await asyncio.sleep(1)
        async with async_session_maker() as db:
            res = await db.execute(select(OrchestratorJob).where(OrchestratorJob.session_id == session_id))
            job = res.scalar_one_or_none()
            if job:
                job_status = job.status
                if job.status == "COMPLETED" or job.status == "FAILED":
                    break
        if i % 5 == 0:
            print(f"Waiting... current status: {job_status}")
            
    print(f"Final Job Status before Commerce test: {job_status}")
    
    print("\n[5] Testing Commerce Engine (ADD_TO_CART)...")
    commerce_payload = {
        "product_id": "bb362054-bbb4-4381-b483-4fbc9603e801",
        "quantity": 1
    }
    commerce_result = await orchestrator.process_commerce_action(session_id, "ADD_TO_CART", commerce_payload)
    print(f"Commerce Engine Result: {commerce_result}")
    
    print("\n[6] Verifying OrchestratorJob State in DB...")
    from app.models.models import OrchestratorJob, CustomerSession
    from sqlalchemy.orm import selectinload
    async with async_session_maker() as db:
        res = await db.execute(select(OrchestratorJob).where(OrchestratorJob.session_id == session_id))
        job = res.scalar_one_or_none()
        if job:
            print(f"DB State Verification: OrchestratorJob {job.id} is in status: {job.status}")
        else:
            print("DB State Verification: Job not found!")
            
        session_res = await db.execute(
            select(CustomerSession)
            .options(selectinload(CustomerSession.customer))
            .where(CustomerSession.session_id == session_id)
        )
        session_record = session_res.scalar_one_or_none()
        print(f"DEBUG DB Customer: {session_record.customer.id if session_record and session_record.customer else 'None'}, Telegram ID: {session_record.customer.telegram_chat_id if session_record and session_record.customer else 'None'}")
    
    print("\nOrchestration Test Completed.")

if __name__ == "__main__":
    asyncio.run(test_full_orchestration())
