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
            
            output = await intent_agent.analyze_intent_structured(structured_input, session_id)
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
        from app.core.telemetry import trace
        try:
            async with async_session_maker() as db:
                res = await db.execute(select(OrchestratorJob).where(OrchestratorJob.id == job_id))
                job = res.scalar_one_or_none()
                if job:
                    job.status = "PRODUCT_INTELLIGENCE_PROCESSING"
                    await db.commit()
            
            logger.info(f"Orchestrator triggering Product Intelligence for session {session_id}")
            pi_agent = ProductIntelligenceAgent()
            
            # Run product intelligence
            async with trace("n_orchestrator", "orchestrator", session_id) as t:
                t.add_event("Calling Product Intelligence Agent")
                recommendations = await pi_agent.generate_recommendations(requirement, session_id)
            
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
                
                # Fallback for testing to ensure Telegram always works in Demo
                if not chat_id:
                    logger.warning(f"No Telegram chat ID found for customer. Using fallback test ID.")
                    chat_id = "2019487070"  # Test telegram account ID from DB dump
                
                if job:
                    job.product_recommendations = recs_dict
                    job.status = "PRODUCT_RECOMMENDATIONS_READY"
                    await db.commit()

            # Send rich product cards to Telegram asynchronously
            if chat_id:
                telegram = get_telegram_provider()
                products = recs_dict.get("recommendations", [])
                summary = recs_dict.get("recommendation_summary") or recs_dict.get("comparison_summary", "Here are some recommendations for you!")
                
                # Run telegram sends in background so we don't block
                import asyncio
                async def send_to_telegram(chat_id, summary, products, session_id):
                    from app.core.telemetry import trace
                    import time
                    
                    async with trace("n_telegram", "engine", session_id) as t:
                        t.set_input({
                            "chat_id": chat_id,
                            "summary": summary,
                            "products_count": len(products),
                            "products": products
                        })
                        t.add_event(f"Sending {len(products)} products to Telegram")
                        
                        start_time = time.time()
                        await telegram.send_recommendation_summary(chat_id, summary, products)
                        
                        for p in products:
                            t.add_event(f"Sending card for {p.get('product_name')}")
                            await telegram.send_product_card(chat_id, p)
                            
                        end_time = time.time()
                        t.add_tool_call("telegram", "send_messages", f"Sent summary + {len(products)} cards", start_time, end_time, "SUCCESS")
                        t.set_output({"status": "Sent successfully"})
                        
                asyncio.create_task(send_to_telegram(chat_id, recs_dict.get("recommendation_summary", ""), products, session_id))
                logger.info(f"Orchestrator successfully routed recommendations to Telegram asynchronously for {session_id}")
            else:
                logger.info(f"No Telegram chat ID found for session {session_id}. Recommendations generated but not sent.")

            # We dispatch the result asynchronously to the voice agent via event queue
            from app.integrations.voice.events import push_voice_event
            await push_voice_event(session_id, "PRODUCT_RECOMMENDATIONS_READY", recs_dict)
            return recs_dict

        except Exception as e:
            logger.error(f"Failed to handle product recommendations: {e}")
            await self._mark_failed(job_id, str(e))
            return {"status": "failed", "error": str(e)}


    async def process_commerce_action(self, session_id: str, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Receives commerce requests (e.g. from Telegram callback query) and dispatches them.
        """
        from app.services.commerce.engine import CommerceEngine
        engine = CommerceEngine()
        
        # Look up customer_id
        from app.models.models import CustomerSession
        from sqlalchemy.future import select
        async with async_session_maker() as db:
            res = await db.execute(select(CustomerSession).where(CustomerSession.session_id == session_id))
            session_rec = res.scalar_one_or_none()
            customer_id = session_rec.user_id if session_rec else None
            
        token = None
        if customer_id:
            import jwt
            from datetime import datetime, timedelta, timezone
            from app.core.config import settings
            expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
            to_encode = {"sub": str(customer_id), "exp": expire}
            # We use the same JWT secret as Demo App to authenticate the request as the user!
            token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm="HS256")
        
        # We pass the generated token so the Demo App can add the product directly to the user's cart instead of an anonymous session cart.
        if action == "ADD_TO_CART":
            product_id = payload.get("product_id")
            quantity = payload.get("quantity", 1)
            
            result = await engine.add_to_cart(
                session_id=session_id,
                product_id=product_id,
                quantity=quantity,
                token=token
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
        job_id = None
        async with async_session_maker() as db:
            res = await db.execute(select(OrchestratorJob).where(OrchestratorJob.session_id == session_id))
            job = res.scalar_one_or_none()
            if not job:
                logger.warning(f"No job found for session {session_id}. Creating an ad-hoc OrchestratorJob for voice session.")
                job_id = str(uuid.uuid4())
                job = OrchestratorJob(
                    id=job_id,
                    session_id=session_id,
                    status="PRODUCT_RECOMMENDATION_REQUESTED"
                )
                db.add(job)
            else:
                job.status = "PRODUCT_RECOMMENDATION_REQUESTED"
                job_id = str(job.id)
            await db.commit()
            
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

    async def handle_product_added_to_cart(self, session_id: str):
        """
        Triggered when the agent successfully adds the product to cart and ends call.
        """
        logger.info(f"Product added to cart. Updating workflow status for session {session_id}.")
        async with async_session_maker() as db:
            res = await db.execute(select(OrchestratorJob).where(OrchestratorJob.session_id == session_id))
            job = res.scalar_one_or_none()
            if job:
                job.status = "ADDED_TO_CART"
                await db.commit()

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
