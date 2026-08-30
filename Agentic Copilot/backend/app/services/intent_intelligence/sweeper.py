import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy.future import select

from app.core.database import async_session_maker
from app.models.models import CustomerSession
from app.services.intent_intelligence.session import finalize_session
from app.core.config import settings

logger = logging.getLogger(__name__)

async def _sweep_idle_sessions():
    idle_timeout = getattr(settings, "SESSION_IDLE_TIMEOUT_SECONDS", 1800)
    
    while True:
        try:
            await asyncio.sleep(60) # Run every minute
            
            now = datetime.utcnow()
            
            async with async_session_maker() as db:
                # Find ACTIVE sessions
                res = await db.execute(select(CustomerSession).where(CustomerSession.status == "ACTIVE"))
                active_sessions = res.scalars().all()
                
                for s in active_sessions:
                    if s.last_active:
                        try:
                            # last_active is e.g. '2026-08-30T10:32:00Z'
                            last_active_time = datetime.fromisoformat(s.last_active.replace("Z", "+00:00")).replace(tzinfo=None)
                            delta = (now - last_active_time).total_seconds()
                            if delta > idle_timeout:
                                logger.info(f"Session {s.session_id} is idle ({delta}s > {idle_timeout}s). Finalizing.")
                                await finalize_session(s.session_id, db, reason="Idle Timeout")
                        except Exception as e:
                            logger.error(f"Error parsing last_active for {s.session_id}: {e}")
                            
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in sweeper loop: {e}")

_sweeper_task = None

def start_sweeper():
    global _sweeper_task
    loop = asyncio.get_running_loop()
    _sweeper_task = loop.create_task(_sweep_idle_sessions())
    logger.info("Intent Intelligence Sweeper started.")

async def stop_sweeper():
    global _sweeper_task
    if _sweeper_task:
        _sweeper_task.cancel()
        try:
            await _sweeper_task
        except asyncio.CancelledError:
            pass
        logger.info("Intent Intelligence Sweeper stopped.")
