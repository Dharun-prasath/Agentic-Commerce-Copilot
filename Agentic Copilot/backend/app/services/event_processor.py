import logging
from sqlalchemy import select
from app.core.database import async_session_maker
from app.graph.orchestrator import run_copilot_graph
from app.models.models import BehaviorEvent

logger = logging.getLogger(__name__)

async def process_event_background(session_id: str):
    """
    Background task to process events via LangGraph.
    Fetches the full event history for the session and invokes the orchestrator.
    """
    logger.info(f"Processing events in background for session {session_id}")
    try:
        async with async_session_maker() as db_session:
            stmt = select(BehaviorEvent).where(BehaviorEvent.session_id == session_id).order_by(BehaviorEvent.created_at.asc())
            result = await db_session.execute(stmt)
            events = result.scalars().all()
            
            # Format events for the LangGraph state
            event_list = [
                {
                    "event_type": e.event_type,
                    "product_id": e.product_id,
                    "category_id": e.category_id,
                    "order_id": e.order_id,
                    "event_metadata": e.event_metadata,
                }
                for e in events
            ]
            
        # Invoke LangGraph
        from app.graph.orchestrator import run_copilot_graph
        # We pass the events to the graph state
        await run_copilot_graph(session_id, {"session_id": session_id, "events": event_list})
        
        logger.info(f"Finished LangGraph execution for session {session_id}")
        
    except Exception as e:
        logger.error(f"Error processing events for session {session_id}: {e}", exc_info=True)
