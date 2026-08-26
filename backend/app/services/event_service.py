"""
Event tracking service — fire-and-forget, never blocks shopping operations.

Design principles:
1. Business operations run first, events track after.
2. Event failures are logged but never propagated to the caller.
3. The Event table is append-only; never update or delete events.
4. All 19 event types are supported.
5. Rich metadata for future Intent Agent consumption.
"""
import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Event, EventType
from app.schemas.commerce import EventCreate, EventOut

logger = logging.getLogger(__name__)


class EventService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def track(self, event: EventCreate) -> Optional[EventOut]:
        """
        Track a single event. Never raises — failures are logged silently.
        Returns the created EventOut, or None on failure.
        """
        try:
            db_event = Event(
                event_type=event.event_type,
                session_id=event.session_id,
                user_id=event.user_id,
                product_id=event.product_id,
                category_id=event.category_id,
                order_id=event.order_id,
                event_metadata=event.metadata or {},
            )
            self.db.add(db_event)
            await self.db.flush()
            return EventOut(
                id=db_event.id,
                event_type=db_event.event_type.value,
                session_id=db_event.session_id,
                user_id=db_event.user_id,
                product_id=db_event.product_id,
                category_id=db_event.category_id,
                order_id=db_event.order_id,
                metadata=db_event.event_metadata or {},
                created_at=db_event.created_at.isoformat() if db_event.created_at else "",
            )
        except Exception as exc:
            logger.error("Event tracking failed (non-critical): %s", exc, exc_info=True)
            return None

    async def get_events(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[EventOut]:
        """
        Query events — used by the Agentic Commerce Copilot.
        Supports filtering by session, user, and event type.
        """
        from sqlalchemy import select
        query = select(Event).order_by(Event.created_at.desc())
        if session_id:
            query = query.where(Event.session_id == session_id)
        if user_id:
            query = query.where(Event.user_id == user_id)
        if event_type:
            try:
                et = EventType(event_type)
                query = query.where(Event.event_type == et)
            except ValueError:
                pass
        query = query.offset(offset).limit(limit)
        result = await self.db.execute(query)
        events = result.scalars().all()
        return [
            EventOut(
                id=e.id,
                event_type=e.event_type.value,
                session_id=e.session_id,
                user_id=e.user_id,
                product_id=e.product_id,
                category_id=e.category_id,
                order_id=e.order_id,
                metadata=e.event_metadata or {},
                created_at=e.created_at.isoformat() if e.created_at else "",
            )
            for e in events
        ]
