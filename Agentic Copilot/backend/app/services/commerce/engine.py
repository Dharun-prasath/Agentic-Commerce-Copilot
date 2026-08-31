import logging
from typing import Dict, Any

from app.integrations.demo_app.client import DemoCommerceClient

logger = logging.getLogger(__name__)

class CommerceEngine:
    """
    Deterministic, rule-based service for executing commerce actions.
    No LLM is used here.
    """
    
    def __init__(self):
        self.demo_client = DemoCommerceClient()
        
    async def add_to_cart(self, session_id: str, product_id: str, quantity: int = 1) -> Dict[str, Any]:
        """
        Safely adds a product to the user's cart in the Demo App.
        """
        logger.info(f"CommerceEngine adding product {product_id} to cart for session {session_id}")
        
        if not product_id:
            return {
                "success": False,
                "error": {
                    "code": "MISSING_PRODUCT_ID",
                    "message": "A valid product ID is required to add to cart."
                }
            }
            
        try:
            # Add to cart via REST API using session_id
            response = await self.demo_client.add_to_cart(
                session_id=session_id,
                product_id=product_id,
                quantity=quantity
            )
            
            return {
                "success": True,
                "action": "ADD_TO_CART",
                "session_id": session_id,
                "product_id": product_id,
                "message": "Product successfully added to cart",
                "details": response
            }
            
        except Exception as e:
            logger.error(f"CommerceEngine failed to add to cart: {e}")
            return {
                "success": False,
                "error": {
                    "code": "COMMERCE_API_ERROR",
                    "message": str(e)
                }
            }
