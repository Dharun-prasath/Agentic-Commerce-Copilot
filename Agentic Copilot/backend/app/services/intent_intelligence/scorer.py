import logging
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.models.models import BehaviorEvent, CustomerSession, IntentScoreHistory

logger = logging.getLogger(__name__)

# Base Rule Weights
SCORING_RULES = {
    "PRODUCT_SEARCHED": 5,
    "PRODUCT_VIEWED": 5,
    "PRODUCT_VIEW_DURATION": 10,
    "PRODUCT_DETAILS_VIEWED": 5,
    "PRODUCT_IMAGE_VIEWED": 2,
    "PRODUCT_SPECS_VIEWED": 8,
    "PRODUCT_FEATURES_VIEWED": 7,
    "PRODUCT_REVIEWS_VIEWED": 8,
    "WISHLIST_ADDED": 15,
}

async def process_event_for_intent(event: BehaviorEvent, session: CustomerSession, db: AsyncSession):
    """
    Evaluates a single event and updates the live intent score deterministically.
    Prevents duplicate scoring for the same exact action on the same product.
    """
    if session.status == "TERMINATED":
        logger.info(f"Ignoring event {event.id} - Session {session.session_id} is already terminated.")
        return

    score_delta = 0
    signal = ""
    reason = ""

    # Base rule check
    event_type = event.event_type
    
    # Simple anti-spam: check if this exact event type + product id was already scored in this session
    stmt = select(func.count(IntentScoreHistory.id)).where(
        IntentScoreHistory.session_id == session.session_id,
        IntentScoreHistory.signal == event_type,
    )
    # If product_id exists, we filter by reason containing the product id
    if event.product_id:
        stmt = stmt.where(IntentScoreHistory.reason.like(f"%{event.product_id}%"))
    
    result = await db.execute(stmt)
    already_scored_count = result.scalar() or 0

    if already_scored_count == 0 and event_type in SCORING_RULES:
        score_delta = SCORING_RULES[event_type]
        signal = event_type
        reason = f"First time {event_type} " + (f"for product {event.product_id}" if event.product_id else "in session")
    elif already_scored_count > 0 and event_type in SCORING_RULES:
        # Diminishing returns or zero score for repeated exact actions
        # For this implementation, we just cap it at 0 to prevent runaway scores
        logger.debug(f"Event {event_type} for {event.product_id} already scored. Ignoring.")
        
    # Check for Multiple products viewed
    if event_type == "PRODUCT_VIEWED":
        # Check how many distinct products viewed
        stmt_distinct = select(func.count(func.distinct(BehaviorEvent.product_id))).where(
            BehaviorEvent.session_id == session.session_id,
            BehaviorEvent.event_type == "PRODUCT_VIEWED"
        )
        dist_res = await db.execute(stmt_distinct)
        distinct_count = dist_res.scalar() or 0
        
        if distinct_count == 2 and already_scored_count == 0:
            # They just viewed their 2nd distinct product!
            score_delta += 10
            signal = "MULTIPLE_PRODUCT_VIEW"
            reason = "Customer viewed multiple distinct products"
            
    if score_delta > 0:
        previous_score = session.current_intent_score or 0.0
        new_score = previous_score + score_delta
        
        # Update Session
        session.current_intent_score = new_score
        threshold = session.intent_threshold if session.intent_threshold is not None else 50.0
        if new_score >= threshold and not session.threshold_reached:
            session.threshold_reached = True
            
        # Record History
        history = IntentScoreHistory(
            id=str(uuid.uuid4()),
            session_id=session.session_id,
            event_id=event.id,
            previous_score=previous_score,
            score_delta=score_delta,
            new_score=new_score,
            signal=signal or event_type,
            reason=reason
        )
        db.add(history)
        
        # We don't commit here, the caller (events.py) commits the transaction.
        
        logger.info(f"Intent Score updated for {session.session_id}: {previous_score} -> {new_score} (+{score_delta}) [{signal}]")
