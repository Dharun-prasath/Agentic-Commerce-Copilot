from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class AnalyticsOverview(BaseModel):
    total_sessions: int
    active_sessions: int
    high_intent_sessions: int
    calls_triggered: int

@router.get("/overview", response_model=AnalyticsOverview)
async def get_overview():
    # Placeholder for actual DB aggregations
    return AnalyticsOverview(
        total_sessions=150,
        active_sessions=12,
        high_intent_sessions=3,
        calls_triggered=1
    )
