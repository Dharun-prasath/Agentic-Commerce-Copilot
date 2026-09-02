import logging
import uuid
import asyncio
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.core.database import async_session_maker
from app.models.models import OrchestratorJob, CustomerSession, IntentAssessment
from app.agents.product_intelligence.agent import ProductIntelligenceAgent
from app.agents.intent.agent import IntentAgent
from app.services.intent_intelligence.session import build_session_summary
from app.integrations.telegram.provider import get_telegram_provider
from app.services.commerce.engine import CommerceEngine
import time
import asyncio

_bg_tasks = set()

logger = logging.getLogger(__name__)

class OrchestratorService:
    """
    Central, deterministic, rule-based Orchestrator.
    Does not use LLMs directly. Maintains workflow state.
    """
    
    async def handle_session_terminated(self, session_id: str):
        """
        Called when a session is terminated. Evaluates if the Intent Agent should be triggered.
        """
        async with async_session_maker() as db:
            res = await db.execute(select(CustomerSession).where(CustomerSession.session_id == session_id))
            session = res.scalar_one_or_none()
            
            if not session:
                logger.error(f"Orchestrator couldn't find session {session_id}")
                return
                
            if session.current_intent_score >= session.intent_threshold:
                logger.info(f"Orchestrator: Session {session_id} met intent threshold ({session.current_intent_score} >= {session.intent_threshold}). Triggering Intent Agent.")
                
                # Create job
                res_job = await db.execute(select(OrchestratorJob).where(OrchestratorJob.session_id == session_id))
                job = res_job.scalar_one_or_none()
                if not job:
                    job = OrchestratorJob(
                        id=str(uuid.uuid4()),
                        session_id=session_id,
                        status="QUEUED"
                    )
                    db.add(job)
                else:
                    if job.status not in ["COMPLETED", "CUSTOMER_NOT_INTERESTED", "FAILED"]:
                        job.status = "QUEUED"
                await db.commit()
                
                # Intent agent is now triggered by QueueManager, so we no longer create the task here.
            else:
                logger.info(f"Orchestrator: Session {session_id} ended WITHOUT meeting intent threshold. Workflow completed.")


    async def _trigger_intent_agent(self, session_id: str, job_id: str):
        """
        Runs the Intent Agent and passes output to process_intent_output.
        """
        try:
            async with async_session_maker() as db:
                structured_input = await build_session_summary(session_id, db)
                
            intent_agent = IntentAgent()
            start_llm = time.time()
            
            output = await intent_agent.analyze_intent_structured(structured_input)
            latency_ms = (time.time() - start_llm) * 1000
            logger.info(f"Orchestrator: Intent Agent completed for {session_id} in {latency_ms:.2f}ms")
            
            async with async_session_maker() as db:
                assessment = IntentAssessment(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    intent_score=structured_input.get("intent_score", {}).get("final_score", 0.0),
                    intent_category=output.intent_category,
                    confidence=output.confidence,
                    signals=structured_input.get("behaviour_signals", []),
                    recommended_action=output.recommended_action,
                    agent_output=output.model_dump()
                )
                db.add(assessment)
                await db.commit()
                
            # Continue workflow
            await self.process_intent_output(session_id, output)
            
        except Exception as e:
            logger.error(f"Orchestrator: Failed to trigger Intent Agent for {session_id}: {e}")
            await self._mark_failed(job_id, str(e))

    
    async def process_intent_output(self, session_id: str, intent_output: Any):
        """
        Entry point after Intent Agent completes.
        Maps intent to a mock customer requirement and triggers Product Intelligence.
        """
        async with async_session_maker() as db:
            # 1. Create or get Orchestrator Job
            res = await db.execute(
                select(OrchestratorJob).where(OrchestratorJob.session_id == session_id)
            )
            job = res.scalar_one_or_none()
            
            if not job:
                job = OrchestratorJob(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    status="SALES_CONSULTANT_TRIGGERED"
                )
                db.add(job)
            else:
                if job.status not in ["INTENT_RECEIVED", "FAILED", "TRIGGERING_INTENT_AGENT", "SALES_CONSULTANT_TRIGGERED"]:
                    logger.info(f"Orchestrator Job {job.id} already processed intent. Status: {job.status}")
                    return
            
            job.status = "SALES_CONSULTANT_TRIGGERED"
            await db.commit()

        # Trigger Electron call
        logger.info(f"Orchestrator: Triggering Sales Consultant (Electron) for session {session_id}.")
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                await client.post("http://127.0.0.1:3456/simulate", json={"session_id": session_id})
        except Exception as e:
            logger.error(f"Orchestrator failed to trigger Electron app: {e}")


    async def _trigger_product_intelligence(self, job_id: str, session_id: str, requirement: Dict[str, Any]):
        """
        Triggers Product Intelligence Agent in the background.
        """
        try:
            async with async_session_maker() as db:
                res = await db.execute(select(OrchestratorJob).where(OrchestratorJob.id == job_id))
                job = res.scalar_one_or_none()
                if job:
                    job.status = "PRODUCT_INTELLIGENCE_PROCESSING"
                    await db.commit()
            
            logger.info(f"Orchestrator triggering Product Intelligence for session {session_id}")
            pi_agent = ProductIntelligenceAgent()
            
            # Run product intelligence (will be refactored to take structured requirement)
            recommendations = await pi_agent.generate_recommendations(requirement)
            
            return await self._handle_product_recommendations(job_id, session_id, recommendations)
            
        except Exception as e:
            logger.error(f"Failed to trigger product intelligence: {e}")
            await self._mark_failed(job_id, str(e))
            return {"status": "failed", "error": str(e)}


    async def _handle_product_recommendations(self, job_id: str, session_id: str, recommendations: Any):
        """
        Receives output from Product Intelligence and routes to Telegram.
        """
        try:
            # Handle Pydantic model
            if hasattr(recommendations, 'model_dump'):
                recs_dict = recommendations.model_dump()
            elif isinstance(recommendations, dict):
                recs_dict = recommendations
            else:
                recs_dict = {}

            async with async_session_maker() as db:
                res = await db.execute(select(OrchestratorJob).where(OrchestratorJob.id == job_id))
                job = res.scalar_one_or_none()
                
                # Fetch customer info for Telegram
                session_res = await db.execute(
                    select(CustomerSession)
                    .options(selectinload(CustomerSession.customer))
                    .where(CustomerSession.session_id == session_id)
                )
                session_record = session_res.scalar_one_or_none()
                
                chat_id = None
                if session_record and session_record.customer and session_record.customer.telegram_chat_id:
                    chat_id = session_record.customer.telegram_chat_id
                
                if job:
                    job.product_recommendations = recs_dict
                    job.status = "PRODUCT_RECOMMENDATIONS_READY"
                    await db.commit()

            # Send rich product cards to Telegram asynchronously
            if chat_id:
                telegram = get_telegram_provider()
                products = recs_dict.get("recommendations", [])
                summary = recs_dict.get("recommendation_summary") or recs_dict.get("comparison_summary", "Here are some recommendations for you!")
                
                # Use module-level _bg_tasks
                global _bg_tasks
                task = asyncio.create_task(telegram.send_recommendation_summary(chat_id, summary, products))
                _bg_tasks.add(task)
                task.add_done_callback(_bg_tasks.discard)
                logger.info(f"Orchestrator successfully routed recommendations to Telegram asynchronously for {session_id}")
            else:
                logger.info(f"No Telegram chat ID found for session {session_id}. Recommendations generated but not sent.")

            # We dispatch the result asynchronously to the voice agent via event queue
            from app.integrations.voice.events import push_voice_event
            push_voice_event(session_id, "PRODUCT_RECOMMENDATIONS_READY", recs_dict)
            return recs_dict

        except Exception as e:
            logger.error(f"Failed to handle product recommendations: {e}")
            await self._mark_failed(job_id, str(e))
            return {"status": "failed", "error": str(e)}


    async def process_commerce_action(self, session_id: str, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Receives commerce requests (e.g. from Telegram callback query) and dispatches them.
        """
        engine = CommerceEngine()
        
        # We use X-Session-Id directly as the 'token' equivalent in the current Demo App implementation
        # The demo app matches cart by X-Session-Id header.
        if action == "ADD_TO_CART":
            product_id = payload.get("product_id")
            quantity = payload.get("quantity", 1)
            
            result = await engine.add_to_cart(
                session_id=session_id,
                product_id=product_id,
                quantity=quantity
            )
            return result
        else:
            return {
                "success": False,
                "error": {
                    "code": "INVALID_ACTION",
                    "message": f"Action {action} is not supported by the Commerce Engine in this phase."
                }
            }


    async def _mark_failed(self, job_id: str, error: str):
        async with async_session_maker() as db:
            res = await db.execute(select(OrchestratorJob).where(OrchestratorJob.id == job_id))
            job = res.scalar_one_or_none()
            if job:
                job.status = "FAILED"
                job.error = error
                await db.commit()

    async def handle_product_recommendation_requested(self, session_id: str, requirements: Dict[str, Any]):
        """
        Triggered by Sales Consultant when enough info is gathered.
        """
        async with async_session_maker() as db:
            res = await db.execute(select(OrchestratorJob).where(OrchestratorJob.session_id == session_id))
            job = res.scalar_one_or_none()
            if not job:
                logger.error(f"Cannot find job for session {session_id} to request PI.")
                return {"status": "error"}
            job.status = "PRODUCT_RECOMMENDATION_REQUESTED"
            await db.commit()
            job_id = job.id
            
        return await self._trigger_product_intelligence(job_id, session_id, requirements)

    async def handle_product_confirmed(self, session_id: str, product_id: str):
        """
        Triggered by Sales Consultant when customer explicitly confirms a product.
        """
        logger.info(f"Customer confirmed product {product_id} for session {session_id}. Triggering Commerce Engine.")
        
        async with async_session_maker() as db:
            res = await db.execute(select(OrchestratorJob).where(OrchestratorJob.session_id == session_id))
            job = res.scalar_one_or_none()
            if job:
                job.status = "COMMERCE_PROCESSING"
                await db.commit()
                
        # Wait for commerce action to complete
        result = await self.process_commerce_action(session_id, "ADD_TO_CART", {"product_id": product_id, "quantity": 1})
        
        async with async_session_maker() as db:
            res = await db.execute(select(OrchestratorJob).where(OrchestratorJob.session_id == session_id))
            job = res.scalar_one_or_none()
            if job:
                job.status = "COMMERCE_COMPLETED"
                await db.commit()
                
        # Push event to voice queue so the Sales Consultant knows the result
        from app.integrations.voice.events import push_voice_event
        await push_voice_event(session_id, "COMMERCE_RESULT", result)

    async def handle_customer_not_interested(self, session_id: str):
        """
        Triggered by Sales Consultant when customer rejects/ends call.
        """
        logger.info(f"Customer not interested. Ending workflow for session {session_id}.")
        async with async_session_maker() as db:
            res = await db.execute(select(OrchestratorJob).where(OrchestratorJob.session_id == session_id))
            job = res.scalar_one_or_none()
            if job:
                job.status = "CUSTOMER_NOT_INTERESTED"
                await db.commit()

    async def handle_call_disconnected(self, session_id: str):
        """
        Triggered when the voice websocket disconnects abruptly or normally.
        """
        logger.info(f"Voice call disconnected for session {session_id}. Verifying job status.")
        async with async_session_maker() as db:
            res = await db.execute(select(OrchestratorJob).where(OrchestratorJob.session_id == session_id))
            job = res.scalar_one_or_none()
            if job and job.status not in ["COMPLETED", "CUSTOMER_NOT_INTERESTED", "FAILED"]:
                logger.info(f"Job {job.id} was in {job.status}. Marking as COMPLETED due to call disconnect.")
                job.status = "COMPLETED"
                await db.commit()

    async def retry_session(self, session_id: str):
        """
        Triggered when RETRY is clicked. Clears active status and resets to QUEUED.
        """
        logger.info(f"Retrying session {session_id}. Resetting job to QUEUED.")
        async with async_session_maker() as db:
            res = await db.execute(select(OrchestratorJob).where(OrchestratorJob.session_id == session_id))
            job = res.scalar_one_or_none()
            
            if not job:
                job = OrchestratorJob(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    status="QUEUED"
                )
                db.add(job)
            else:
                job.status = "QUEUED"
                job.error = None
                
            await db.commit()
