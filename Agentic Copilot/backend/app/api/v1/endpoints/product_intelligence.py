from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from app.agents.product_intelligence.agent import ProductIntelligenceAgent
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/recommend")
async def get_product_recommendations(mock_requirement: Dict[str, Any]):
    """
    Internal API to manually trigger the Product Intelligence Agent.
    Requires a Mock Customer Requirement JSON payload.
    """
    try:
        agent = ProductIntelligenceAgent()
        result = await agent.generate_recommendations(mock_requirement)
        
        # Pydantic model dump
        return result.model_dump()
    except Exception as e:
        logger.error(f"Failed to generate recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))
