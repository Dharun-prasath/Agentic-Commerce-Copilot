from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.models.models import CustomerSession, IntentScoreHistory, IntentAgentJob, IntentAssessment

router = APIRouter()

@router.get("/{session_id}")
async def get_session_intent(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CustomerSession).where(CustomerSession.session_id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    history_res = await db.execute(
        select(IntentScoreHistory)
        .where(IntentScoreHistory.session_id == session_id)
        .order_by(IntentScoreHistory.created_at)
    )
    history_records = history_res.scalars().all()
    
    # Get Queue Job Status
    job_res = await db.execute(
        select(IntentAgentJob).where(IntentAgentJob.session_id == session_id)
    )
    job = job_res.scalar_one_or_none()
    
    # Get Intent Assessment Output
    assessment_res = await db.execute(
        select(IntentAssessment).where(IntentAssessment.session_id == session_id)
    )
    assessment = assessment_res.scalar_one_or_none()

    intent_agent_status = "WAITING FOR SESSION TERMINATION"
    if session.status == "TERMINATED":
        if not session.threshold_reached:
            intent_agent_status = "NOT TRIGGERED"
        else:
            intent_agent_status = job.status if job else "QUEUED"
            
    return {
        "session_id": session.session_id,
        "current_score": session.current_intent_score,
        "threshold": session.intent_threshold,
        "threshold_reached": session.threshold_reached,
        "status": session.status,
        "intent_agent_status": intent_agent_status,
        "intent_output": assessment.agent_output if assessment and assessment.agent_output else None,
        "history": [
            {
                "timestamp": h.created_at.isoformat() + "Z",
                "previous_score": h.previous_score,
                "score_delta": h.score_delta,
                "new_score": h.new_score,
                "signal": h.signal,
                "reason": h.reason
            }
            for h in history_records
        ]
    }
