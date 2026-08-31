from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
from app.services.orchestrator.service import OrchestratorService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/events")
async def process_orchestrator_event(session_id: str, payload: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Internal API to manually trigger the Orchestrator with an Intent Output payload.
    """
    try:
        orchestrator = OrchestratorService()
        # Fire and forget the orchestrator process so the API returns quickly
        background_tasks.add_task(orchestrator.process_intent_output, session_id, payload)
        
        return {
            "success": True,
            "message": f"Orchestrator job accepted for session {session_id}"
        }
    except Exception as e:
        logger.error(f"Failed to process orchestrator event: {e}")
        raise HTTPException(status_code=500, detail=str(e))
