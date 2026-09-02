import logging
from typing import Dict, Any, Optional

from app.integrations.demo_app.client import DemoCommerceClient

logger = logging.getLogger(__name__)

class CommerceEngine:
    """
    Deterministic, rule-based service for executing commerce actions.
    No LLM is used here.
    """
    
    def __init__(self):
        self.demo_client = DemoCommerceClient()
        
    async def add_to_cart(self, session_id: str, product_id: str, quantity: int = 1, token: Optional[str] = None) -> Dict[str, Any]:
        """
        Safely adds a product to the user's cart in the Demo App.
        """
        from app.core.telemetry import trace
        import time
        
        async with trace("n_commerce", "engine", session_id) as t:
            t.set_input({"product_id": product_id, "quantity": quantity, "token": token})
            t.add_event("Starting Commerce action: add_to_cart")
            
            logger.info(f"CommerceEngine adding product {product_id} to cart for session {session_id}")
            
            if not product_id:
                err_out = {
                    "success": False,
                    "error": {
                        "code": "MISSING_PRODUCT_ID",
                        "message": "A valid product ID is required to add to cart."
                    }
                }
                t.set_output(err_out)
                t.set_error(ValueError("MISSING_PRODUCT_ID"))
                return err_out
                
            try:
                # Get user_id from session to sync with Demo App cart
                from app.core.database import async_session_maker
                from sqlalchemy.future import select
                from app.models.models import CustomerSession
                
                user_id = None
                async with async_session_maker() as db:
                    res = await db.execute(select(CustomerSession).where(CustomerSession.session_id == session_id))
                    db_session = res.scalar_one_or_none()
                    if db_session and db_session.user_id:
                        user_id = db_session.user_id
                        
                # Add to cart via REST API using session_id
                t.add_event("Calling Demo App Cart API")
                start_time = time.time()
                response = await self.demo_client.add_to_cart(
                    session_id=session_id,
                    product_id=product_id,
                    quantity=quantity,
                    token=token,
                    user_id=user_id
                )
                end_time = time.time()
                t.add_tool_call("demo_client", "add_to_cart", {"session_id": session_id, "product_id": product_id, "quantity": quantity, "user_id": user_id}, start_time, end_time, "SUCCESS", response)
                
                out = {
                    "success": True,
                    "action": "ADD_TO_CART",
                    "session_id": session_id,
                    "product_id": product_id,
                    "message": "Product successfully added to cart",
                    "details": response
                }
                t.set_output(out)
                t.add_event("Added to cart successfully")
                return out
                
            except Exception as e:
                logger.error(f"CommerceEngine failed to add to cart: {e}")
                t.add_tool_call("demo_client", "add_to_cart", {"session_id": session_id, "product_id": product_id, "quantity": quantity}, start_time, time.time(), "FAILED", error=str(e))
                err_out = {
                    "success": False,
                    "error": {
                        "code": "COMMERCE_API_ERROR",
                        "message": str(e)
                    }
                }
                t.set_output(err_out)
                t.set_error(e)
                return err_out
