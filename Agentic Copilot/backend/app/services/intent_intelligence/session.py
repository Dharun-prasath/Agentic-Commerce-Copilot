import logging
from datetime import datetime
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, text

from app.models.models import CustomerSession, BehaviorEvent, IntentScoreHistory
from app.agents.intent.agent import IntentAgent

logger = logging.getLogger(__name__)

async def build_session_summary(session_id: str, db: AsyncSession) -> dict:
    # Fetch session
    result = await db.execute(select(CustomerSession).where(CustomerSession.session_id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        return {}

    # Fetch events
    events_res = await db.execute(
        select(BehaviorEvent)
        .where(BehaviorEvent.session_id == session_id)
        .order_by(BehaviorEvent.created_at)
    )
    events = events_res.scalars().all()

    # Fetch score history
    history_res = await db.execute(
        select(IntentScoreHistory)
        .where(IntentScoreHistory.session_id == session_id)
        .order_by(IntentScoreHistory.created_at)
    )
    history = history_res.scalars().all()

    # Aggregations
    searches = []
    products_viewed = {}
    wishlist = []
    behaviour_signals = {
        "specifications_viewed": False,
        "features_viewed": False,
        "reviews_viewed": False,
        "multiple_products_viewed": False
    }

    # Extract unique product IDs
    unique_product_ids = list(set([e.product_id for e in events if e.product_id]))
    product_map = {}
    if unique_product_ids:
        from app.core.database import commerce_engine
        async with commerce_engine.connect() as conn:
            query = text("""
                SELECT p.id, p.name, c.name as category_name, p.price 
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.id = ANY(:ids)
            """)
            res = await conn.execute(query, {"ids": unique_product_ids})
            for row in res.mappings():
                product_map[row["id"]] = {
                    "product_id": row["id"],
                    "product_name": row["name"],
                    "category": row["category_name"],
                    "price": float(row["price"]) if row["price"] else 0.0
                }

    for e in events:
        if e.event_type == "PRODUCT_SEARCHED":
            q = e.event_metadata.get("query")
            if q and q not in searches:
                searches.append(q)
        elif e.event_type == "PRODUCT_VIEWED" and e.product_id:
            if e.product_id not in products_viewed:
                p_info = product_map.get(e.product_id, {"product_id": e.product_id, "product_name": "Unknown Product"})
                products_viewed[e.product_id] = {
                    "product_id": e.product_id,
                    "product_name": p_info.get("product_name"),
                    "category": p_info.get("category"),
                    "price": p_info.get("price"),
                    "view_count": 0
                }
            products_viewed[e.product_id]["view_count"] += 1
        elif e.event_type == "WISHLIST_ADDED" and e.product_id:
            if e.product_id not in [item.get("product_id") if isinstance(item, dict) else item for item in wishlist]:
                p_info = product_map.get(e.product_id, {"product_id": e.product_id, "product_name": "Unknown Product"})
                wishlist.append({
                    "product_id": e.product_id,
                    "product_name": p_info.get("product_name"),
                    "category": p_info.get("category"),
                    "price": p_info.get("price")
                })
        elif e.event_type == "PRODUCT_SPECIFICATIONS_VIEWED":
            behaviour_signals["specifications_viewed"] = True
        elif e.event_type == "PRODUCT_FEATURES_VIEWED":
            behaviour_signals["features_viewed"] = True
        elif e.event_type == "PRODUCT_REVIEW_VIEWED":
            behaviour_signals["reviews_viewed"] = True

    if len(products_viewed) > 1:
        behaviour_signals["multiple_products_viewed"] = True

    duration_seconds = 0
    if events:
        start_time = events[0].created_at
        end_time = events[-1].created_at
        duration_seconds = int((end_time - start_time).total_seconds())

    score_breakdown = [
        {"signal": h.signal, "score": h.score_delta, "reason": h.reason}
        for h in history
    ]

    return {
        "session_id": session.session_id,
        "customer_id": session.user_id or "unknown",
        "session": {
            "duration_seconds": duration_seconds
        },
        "intent_score": {
            "final_score": session.current_intent_score,
            "threshold": session.intent_threshold,
            "threshold_reached": session.threshold_reached
        },
        "searches": searches,
        "products_viewed": list(products_viewed.values()),
        "behaviour_signals": behaviour_signals,
        "wishlist_products": wishlist,
        "score_breakdown": score_breakdown
    }

async def finalize_session(session_id: str, db: AsyncSession, reason: str = "Explicit Termination"):
    """
    Finalizes an intent session. Stops accepting scores.
    """
    result = await db.execute(
        select(CustomerSession)
        .where(CustomerSession.session_id == session_id)
        .with_for_update()
    )
    session = result.scalar_one_or_none()
    if not session or session.status == "TERMINATED":
        return

    session.status = "TERMINATED"
    session.finalized_at = datetime.utcnow().isoformat() + "Z"
    
    if session.current_intent_score and session.current_intent_score >= session.intent_threshold:
        session.threshold_reached = True
    
    # Calculate duration
    events_res = await db.execute(
        select(BehaviorEvent)
        .where(BehaviorEvent.session_id == session_id)
        .order_by(BehaviorEvent.created_at)
    )
    events = events_res.scalars().all()
    duration_seconds = 0
    if events:
        start_time = events[0].created_at
        end_time = events[-1].created_at
        duration_seconds = int((end_time - start_time).total_seconds())

    logger.info(f"Finalizing session {session_id} (Duration: {duration_seconds}s). Score: {session.current_intent_score}. Threshold: {session.intent_threshold}")
    
    await db.commit()
