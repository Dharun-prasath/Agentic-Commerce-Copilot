import asyncio
import logging
from datetime import datetime
import time
from sqlalchemy.future import select

from app.core.database import async_session_maker
from app.models.models import IntentAgentJob, IntentAssessment
from app.agents.intent.agent import IntentAgent
from app.services.intent_intelligence.session import build_session_summary
import uuid

logger = logging.getLogger(__name__)

async def _process_queue():
    while True:
        try:
            await asyncio.sleep(5) # Poll every 5 seconds
            
            async with async_session_maker() as db:
                from datetime import timedelta
                from sqlalchemy import or_
                import uuid

                now = datetime.utcnow()
                now_str = now.isoformat() + "Z"

                # Find oldest QUEUED job, or expired PROCESSING job
                res = await db.execute(
                    select(IntentAgentJob)
                    .where(
                        or_(
                            IntentAgentJob.status == "QUEUED",
                            (IntentAgentJob.status == "PROCESSING") & (IntentAgentJob.lease_until != None) & (IntentAgentJob.lease_until < now_str)
                        )
                    )
                    .order_by(
                        IntentAgentJob.priority.desc(),
                        IntentAgentJob.id.asc()
                    )
                    .limit(1)
                    .with_for_update(skip_locked=True)
                )
                job = res.scalar_one_or_none()
                
                if not job:
                    continue
                
                session_id = job.session_id
                logger.info(f"Queue Worker picked up job {job.id} for session {session_id} (Attempt {job.attempts + 1})")
                
                # Mark as processing
                job.status = "PROCESSING"
                job.started_at = now_str
                job.attempts += 1
                
                # Set lease for 2 minutes
                lease_time = now + timedelta(minutes=2)
                job.lease_until = lease_time.isoformat() + "Z"
                job.worker_id = str(uuid.uuid4())
                await db.commit()
                
                try:
                    # Build structured input
                    structured_input = await build_session_summary(session_id, db)
                    
                    # Call Agent
                    intent_agent = IntentAgent()
                    start_llm = time.time()
                    
                    output = await intent_agent.analyze_intent_structured(structured_input)
                    latency_ms = (time.time() - start_llm) * 1000
                    
                    
                    logger.info(f"Intent Agent completed for {session_id} in {latency_ms:.2f}ms")
                    
                    # Persist exactly into IntentAssessment
                    assessment = IntentAssessment(
                        id=str(uuid.uuid4()),
                        session_id=session_id,
                        intent_score=structured_input.get("final_score", 0.0),
                        intent_category=output.intent_category,
                        confidence=output.confidence,
                        signals=structured_input.get("signals", []),
                        recommended_action=output.recommended_action,
                        agent_output=output.model_dump()
                    )
                    db.add(assessment)
                    
                    # Mark COMPLETED
                    job.status = "COMPLETED"
                    job.completed_at = datetime.utcnow().isoformat() + "Z"
                    await db.commit()
                    

                except Exception as e:
                    logger.error(f"Intent Agent failed for {session_id}: {e}")
                    
                    if job.attempts >= job.max_attempts:
                        job.status = "FAILED"
                        logger.error(f"Job {job.id} reached max attempts ({job.max_attempts}). Marking FAILED.")
                    else:
                        # Allow retry
                        job.status = "QUEUED"
                        job.lease_until = None
                        
                    job.error = str(e)
                    await db.commit()
                    

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in queue worker loop: {e}")

_queue_worker_task = None

def start_queue_worker():
    global _queue_worker_task
    loop = asyncio.get_running_loop()
    _queue_worker_task = loop.create_task(_process_queue())
    logger.info("Intent Agent Queue Worker started.")

async def stop_queue_worker():
    global _queue_worker_task
    if _queue_worker_task:
        _queue_worker_task.cancel()
        try:
            await _queue_worker_task
        except asyncio.CancelledError:
            pass
        logger.info("Intent Agent Queue Worker stopped.")
