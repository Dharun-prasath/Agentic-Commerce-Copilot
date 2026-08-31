from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from app.services.commerce.engine import CommerceEngine
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/cart")
async def internal_add_to_cart(session_id: str, payload: Dict[str, Any]):
    """
    Internal API to manually trigger a cart addition via the Commerce Engine.
    """
    try:
        engine = CommerceEngine()
        product_id = payload.get("product_id")
        quantity = payload.get("quantity", 1)
        
        if not product_id:
            raise HTTPException(status_code=400, detail="product_id is required")
            
        result = await engine.add_to_cart(session_id, product_id, quantity)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
            
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Commerce action failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
