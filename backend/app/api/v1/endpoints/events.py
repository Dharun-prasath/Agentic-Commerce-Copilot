"""Events API — for Agentic Commerce Copilot consumption."""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.commerce import EventCreate, EventOut
from app.services.event_service import EventService

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=Optional[EventOut], status_code=201)
async def track_event(
    data: EventCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Ingest a customer behaviour event.
    
    This endpoint is designed for consumption by the Agentic Commerce Copilot.
    Event tracking never blocks shopping operations — failures are silently logged.
    
    Supported event types:
    - PRODUCT_SEARCHED, PRODUCT_VIEWED, PRODUCT_DETAILS_VIEWED
    - PRODUCT_IMAGE_VIEWED, PRODUCT_SPECIFICATIONS_VIEWED, PRODUCT_REVIEW_VIEWED
    - PRODUCT_COMPARED
    - WISHLIST_ADDED, WISHLIST_REMOVED
    - CART_ITEM_ADDED, CART_ITEM_REMOVED, CART_UPDATED
    - CHECKOUT_STARTED, CHECKOUT_COMPLETED
    - PAYMENT_STARTED, PAYMENT_SUCCESS, PAYMENT_FAILED
    - ORDER_CREATED
    """
    return await EventService(db).track(data)


@router.get("", response_model=List[EventOut])
async def get_events(
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Query stored events.
    Designed for Agentic Commerce Copilot to retrieve customer journey data.
    """
    return await EventService(db).get_events(
        session_id=session_id,
        user_id=user_id,
        event_type=event_type,
        limit=limit,
        offset=offset,
    )
