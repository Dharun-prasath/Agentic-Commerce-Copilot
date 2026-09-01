from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc
from app.core.database import get_db, async_session_maker
from app.core.security import verify_api_key
from app.models.models import CustomerSession, IntentAssessment, Conversation, CommerceAction
import logging
import json
import asyncio
from app.services.observability.graph_builder import build_execution_graph

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(verify_api_key)])

@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    try:
        # Active Sessions
        active_sessions_result = await db.execute(
            select(func.count(CustomerSession.session_id))
            .where(CustomerSession.status != "TERMINATED")
        )
        active_sessions = active_sessions_result.scalar() or 0

        # High Intent Detected
        high_intent_result = await db.execute(
            select(func.count(IntentAssessment.id))
            .where(IntentAssessment.intent_category == "HIGH_PURCHASE_INTENT")
        )
        high_intent_count = high_intent_result.scalar() or 0

        # Calls Triggered (We can approximate with Electron/Voice conversations)
        calls_result = await db.execute(
            select(func.count(Conversation.id))
            .where(Conversation.channel == "ELECTRON_CALL")
        )
        calls_count = calls_result.scalar() or 0

        # Commerce Actions (Instead of mocked revenue)
        commerce_result = await db.execute(
            select(func.count(CommerceAction.id))
            .where(CommerceAction.action_type.in_(["ADD_TO_CART", "PURCHASE", "PAYMENT_LINK_CREATED"]))
        )
        commerce_actions_count = commerce_result.scalar() or 0
        revenue_val = f"{commerce_actions_count}"

        return {
            "active_sessions": str(active_sessions),
            "high_intent": str(high_intent_count),
            "calls_triggered": str(calls_count),
            "revenue": revenue_val
        }
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return {
            "active_sessions": "0",
            "high_intent": "0",
            "calls_triggered": "0",
            "revenue": "₹0"
        }

@router.get("/sessions")
async def get_dashboard_sessions(db: AsyncSession = Depends(get_db)):
    try:
        # Fetch the most recent 10 sessions
        from sqlalchemy.orm import selectinload
        from app.models.models import OrchestratorJob
        
        result = await db.execute(
            select(CustomerSession)
            .options(selectinload(CustomerSession.customer))
            .order_by(desc(CustomerSession.created_at))
            .limit(10)
        )
        sessions = result.scalars().all()
        
        session_ids = [s.session_id for s in sessions]
        jobs_result = await db.execute(
            select(OrchestratorJob).where(OrchestratorJob.session_id.in_(session_ids))
        )
        jobs = {j.session_id: j for j in jobs_result.scalars().all()}
        
        output = []
        for s in sessions:
            score = s.current_intent_score or 0.0
            score_percent = min(100, int(score))
            intent_score = f"{score_percent}%"
            
            is_active = True
            
            if s.status == "TERMINATED":
                if s.threshold_reached:
                    status = "HIGH INTENT • TERMINATED"
                    is_active = "green"
                    job = jobs.get(s.session_id)
                    if job:
                        if job.status == "INTENT_RECEIVED":
                            action_text = "Intent Agent: COMPLETED"
                        elif job.status == "TRIGGERING_INTENT_AGENT":
                            action_text = "Intent Agent: PROCESSING"
                        elif job.status == "PRODUCT_INTELLIGENCE_PROCESSING":
                            action_text = "Product Intelligence: PROCESSING"
                        else:
                            action_text = f"Agent: {job.status}"
                    else:
                        action_text = "Intent Agent: QUEUED"
                else:
                    status = "TERMINATED"
                    is_active = False
                    action_text = "Intent Agent: NOT TRIGGERED"
            elif s.threshold_reached:
                status = "HIGH INTENT"
                is_active = "green"
                action_text = "Intent Agent: NOT TRIGGERED"
            elif score > 0:
                status = "ACTIVE"
                action_text = "Intent Agent: NOT TRIGGERED"
            else:
                status = "INACTIVE"
                is_active = False
                action_text = "Inactive"
            
            # Formatting time (simplified)
            time_str = "Recently"
            if s.created_at:
                time_str = s.created_at.strftime("%H:%M")
                
            user_name = "Anonymous"
            if s.customer and s.customer.name:
                user_name = s.customer.name
            elif s.user_id:
                user_name = s.user_id
                
            output.append({
                "id": s.session_id,
                "user": user_name,
                "intent": intent_score,
                "status": status,
                "action": action_text,
                "time": time_str,
                "active": is_active
            })
            
        return output
    except Exception as e:
        logger.error(f"Error fetching sessions: {e}")
        return []

@router.get("/sessions/{session_id}")
async def get_session_details(session_id: str, db: AsyncSession = Depends(get_db)):
    # This will be used by the Customer 360 panel
    try:
        from app.models.models import ConversationMessage, BehaviorEvent
        
        # Get chat history
        messages_result = await db.execute(
            select(ConversationMessage)
            .join(Conversation)
            .where(Conversation.session_id == session_id)
            .order_by(ConversationMessage.created_at)
        )
        messages = messages_result.scalars().all()
        
        # Get events
        events_result = await db.execute(
            select(BehaviorEvent)
            .where(BehaviorEvent.session_id == session_id)
            .order_by(desc(BehaviorEvent.created_at))
        )
        events = events_result.scalars().all()
        
        # Get cart data from Demo App
        cart_data = None
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                res = await client.get(
                    "http://localhost:8001/api/v1/cart",
                    headers={"x-session-id": session_id}
                )
                if res.status_code == 200:
                    cart_data = res.json()
        except Exception as e:
            logger.error(f"Failed to fetch cart data: {e}")
        
        return {
            "session_id": session_id,
            "messages": [{"sender": m.sender_type, "content": m.content, "time": m.created_at} for m in messages],
            "events": [{"type": e.event_type, "product": e.product_id, "time": e.created_at} for e in events],
            "cart": cart_data
        }
    except Exception as e:
        logger.error(f"Error fetching session details: {e}")
        return {"error": str(e)}

@router.get("/calls")
async def get_dashboard_calls(db: AsyncSession = Depends(get_db)):
    try:
        from sqlalchemy.orm import selectinload
        from app.models.models import OrchestratorJob, CustomerSession
        
        result = await db.execute(
            select(OrchestratorJob)
            .options(selectinload(OrchestratorJob.session).selectinload(CustomerSession.customer))
            .order_by(desc(OrchestratorJob.created_at))
            .limit(50)
        )
        jobs = result.scalars().all()
        
        output = []
        for job in jobs:
            s = job.session
            if not s:
                continue
                
            user_name = "Anonymous"
            if s.customer and s.customer.name:
                user_name = s.customer.name
            elif s.user_id:
                user_name = s.user_id
                
            time_str = job.created_at.strftime("%Y-%m-%d %H:%M") if job.created_at else "Unknown"
            
            output.append({
                "id": job.id,
                "session_id": job.session_id,
                "user": user_name,
                "status": job.status,
                "time": time_str,
                "error": job.error
            })
            
        return output
    except Exception as e:
        logger.error(f"Error fetching calls: {e}")
        return []

@router.get("/queue")
async def get_dashboard_queue(db: AsyncSession = Depends(get_db)):
    try:
        from app.models.models import OrchestratorJob
        
        # High intent sessions that are either processing or waiting
        result = await db.execute(
            select(CustomerSession)
            .where(CustomerSession.threshold_reached == True)
            .order_by(desc(CustomerSession.created_at))
            .limit(20)
        )
        sessions = result.scalars().all()
        
        output = []
        for i, s in enumerate(sessions):
            job_res = await db.execute(select(OrchestratorJob).where(OrchestratorJob.session_id == s.session_id))
            job = job_res.scalar_one_or_none()
            
            queue_status = "WAITING"
            if job:
                if job.status == "COMPLETED" or job.status == "CUSTOMER_NOT_INTERESTED":
                    queue_status = "COMPLETED"
                elif "FAILED" in job.status:
                    queue_status = "FAILED"
                else:
                    queue_status = "RUNNING"
            elif s.status == "TERMINATED":
                queue_status = "TERMINATED"
                
            time_str = s.created_at.strftime("%H:%M:%S") if s.created_at else "Unknown"
            
            output.append({
                "position": i + 1,
                "session_id": s.session_id,
                "status": queue_status,
                "intent_score": s.current_intent_score,
                "time": time_str
            })
            
        return output
    except Exception as e:
        logger.error(f"Error fetching queue: {e}")
        return []

from app.services.orchestrator.queue_manager import QueueManager
from pydantic import BaseModel

class DelayConfig(BaseModel):
    delay_seconds: int

@router.get("/queue/config")
async def get_queue_config():
    return QueueManager.get_instance().get_status()

@router.post("/queue/config")
async def set_queue_config(config: DelayConfig):
    QueueManager.get_instance().set_delay(config.delay_seconds)
    return {"status": "success", "delay": config.delay_seconds}

@router.post("/queue/pause")
async def pause_queue():
    QueueManager.get_instance().pause()
    return {"status": "paused"}

@router.post("/queue/resume")
async def resume_queue():
    QueueManager.get_instance().resume()
    return {"status": "resumed"}

@router.post("/queue/next")
async def start_next_in_queue():
    QueueManager.get_instance().skip_delay()
    return {"status": "skipped_delay"}

@router.post("/execution/{session_id}/retry")
async def retry_session_execution(session_id: str):
    from app.services.orchestrator.service import OrchestratorService
    await OrchestratorService().retry_session(session_id)
    # Also skip delay if queue is empty or this is the current next
    QueueManager.get_instance().skip_delay()
    return {"status": "retrying"}

@router.get("/execution/{session_id}")
async def get_execution_graph(session_id: str, db: AsyncSession = Depends(get_db)):
    try:
        graph = await build_execution_graph(session_id, db)
        return graph
    except Exception as e:
        logger.error(f"Error fetching graph: {e}")
        return {"nodes": [], "edges": []}

@router.get("/execution/{session_id}/stream")
async def stream_execution_graph(session_id: str):
    async def event_generator():
        last_state = ""
        while True:
            try:
                async with async_session_maker() as db:
                    graph = await build_execution_graph(session_id, db)
                    graph_str = json.dumps(graph)
                    if graph_str != last_state:
                        last_state = graph_str
                        yield f"data: {graph_str}\n\n"
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"SSE Error: {e}")
            await asyncio.sleep(1)
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")
