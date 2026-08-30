from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
from pydantic import BaseModel
import uuid

from app.core.database import get_db
from app.models.models import BehaviorEvent, CustomerSession

router = APIRouter()

class EventPayload(BaseModel):
    event_id: Optional[str] = None
    event_type: str
    session_id: str
    user_id: Optional[str] = None
    product_id: Optional[str] = None
    category_id: Optional[str] = None
    order_id: Optional[str] = None
    event_metadata: Dict[str, Any] = {}

from datetime import datetime

@router.post("")
async def ingest_event(
    payload: EventPayload, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    # Ignore anonymous sessions
    if not payload.user_id or payload.user_id == "unknown":
        return {"status": "ignored", "message": "Anonymous sessions are not tracked"}

    # Upsert Customer if user_name is present
    user_name = payload.event_metadata.get("user_name") if payload.event_metadata else None
    if payload.user_id and user_name:
        from app.models.models import Customer
        customer = await db.get(Customer, payload.user_id)
        if not customer:
            customer = Customer(id=payload.user_id, name=user_name)
            db.add(customer)
        elif customer.name != user_name and user_name != "Unknown User":
            customer.name = user_name

    # Upsert CustomerSession
    session_obj = await db.get(CustomerSession, payload.session_id)
    if not session_obj:
        session_obj = CustomerSession(
            session_id=payload.session_id,
            user_id=payload.user_id,
            last_active=datetime.utcnow().isoformat() + "Z"
        )
        db.add(session_obj)
    else:
        # Update user_id if newly provided (even if another user was previously logged in on this session)
        if payload.user_id and session_obj.user_id != payload.user_id:
            session_obj.user_id = payload.user_id
        session_obj.last_active = datetime.utcnow().isoformat() + "Z"

    event_id = payload.event_id or str(uuid.uuid4())
    
    # Strictly Idempotent: Ignore if event_id already exists
    from sqlalchemy.future import select
    existing_event = await db.get(BehaviorEvent, event_id)
    if existing_event:
        return {"status": "success", "event_id": event_id, "current_score": session_obj.current_intent_score, "message": "Idempotent event ignored"}
        
    # Create event
    new_event = BehaviorEvent(
        id=event_id,
        session_id=payload.session_id,
        user_id=payload.user_id,
        event_type=payload.event_type,
        product_id=payload.product_id,
        category_id=payload.category_id,
        order_id=payload.order_id,
        event_metadata=payload.event_metadata
    )
    db.add(new_event)
    
    
    was_threshold_reached = session_obj.threshold_reached
    
    # Process intent score synchronously BEFORE commit, so it runs in same transaction
    from app.services.intent_intelligence.scorer import process_event_for_intent
    await process_event_for_intent(new_event, session_obj, db)
    
    # Auto-finalize removed. Session will remain ACTIVE until explicitly terminated.    
    await db.commit()
    
    return {"status": "success", "event_id": new_event.id, "current_score": session_obj.current_intent_score}

class TerminateSessionPayload(BaseModel):
    session_id: str

@router.post("/terminate")
async def terminate_session(
    payload: TerminateSessionPayload,
    db: AsyncSession = Depends(get_db)
):
    from app.services.intent_intelligence.session import finalize_session
    await finalize_session(payload.session_id, db, reason="Explicit Frontend Termination")
    return {"status": "terminated"}

@router.get("/terminate/{session_id}")
@router.post("/terminate/{session_id}")
async def terminate_session_path(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    from app.services.intent_intelligence.session import finalize_session
    await finalize_session(session_id, db, reason="Explicit Frontend Termination")
    return {"status": "terminated"}
