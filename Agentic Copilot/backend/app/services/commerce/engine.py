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
        Safely adds a product to the user's cart in the Demo App by directly modifying the database.
        """
        from app.core.telemetry import trace
        import time
        import uuid
        import datetime
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
        from app.core.config import settings
        
        async with trace("n_commerce", "engine", session_id) as t:
            t.set_input({"product_id": product_id, "quantity": quantity, "token": token})
            t.add_event("Starting Commerce action: add_to_cart (Direct DB)")
            
            logger.info(f"CommerceEngine forcefully adding product {product_id} to cart for session {session_id}")
            
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
                # Get user_id from session
                from app.core.database import async_session_maker
                from sqlalchemy.future import select
                from app.models.models import CustomerSession
                
                user_id = None
                async with async_session_maker() as db:
                    res = await db.execute(select(CustomerSession).where(CustomerSession.session_id == session_id))
                    db_session = res.scalar_one_or_none()
                    if db_session and db_session.user_id:
                        user_id = db_session.user_id
                        
                t.add_event("Executing direct DB cart insertion")
                start_time = time.time()
                
                # Connect to Demo App DB directly
                engine = create_async_engine(settings.COMMERCE_DATABASE_URL)
                
                async with engine.begin() as conn:
                    # Verify product
                    res = await conn.execute(text("SELECT id, name FROM products WHERE id = :pid"), {"pid": product_id})
                    product = res.fetchone()
                    if not product:
                        raise ValueError(f"Product {product_id} not found in catalog")
                        
                    cart_id = None
                    
                    if user_id:
                        # Find specific user cart
                        res = await conn.execute(text("SELECT id FROM carts WHERE user_id = :uid LIMIT 1"), {"uid": str(user_id)})
                        cart = res.fetchone()
                        if cart:
                            cart_id = cart.id
                        else:
                            cart_id = str(uuid.uuid4())
                            await conn.execute(
                                text("INSERT INTO carts (id, user_id, session_id, created_at, updated_at) VALUES (:cid, :uid, :sid, :now, :now)"),
                                {"cid": cart_id, "uid": str(user_id), "sid": str(uuid.uuid4()), "now": datetime.datetime.utcnow()}
                            )
                    else:
                        # Find most recently active cart as a fallback for anonymous hackathon users
                        res = await conn.execute(text("SELECT id FROM carts ORDER BY created_at DESC LIMIT 1"))
                        cart = res.fetchone()
                        if cart:
                            cart_id = cart.id
                        else:
                            cart_id = str(uuid.uuid4())
                            await conn.execute(
                                text("INSERT INTO carts (id, session_id, created_at, updated_at) VALUES (:cid, :sid, :now, :now)"),
                                {"cid": cart_id, "sid": "orchestrator-fallback-session", "now": datetime.datetime.utcnow()}
                            )
                            
                    # Add item or increment
                    res = await conn.execute(
                        text("SELECT id, quantity FROM cart_items WHERE cart_id = :cid AND product_id = :pid"),
                        {"cid": cart_id, "pid": product_id}
                    )
                    cart_item = res.fetchone()
                    
                    if cart_item:
                        new_qty = cart_item.quantity + quantity
                        await conn.execute(
                            text("UPDATE cart_items SET quantity = :qty WHERE id = :item_id"),
                            {"qty": new_qty, "item_id": cart_item.id}
                        )
                    else:
                        item_id = str(uuid.uuid4())
                        await conn.execute(
                            text("INSERT INTO cart_items (id, cart_id, product_id, quantity) VALUES (:iid, :cid, :pid, :qty)"),
                            {"iid": item_id, "cid": cart_id, "pid": product_id, "qty": quantity}
                        )
                
                # Close engine
                await engine.dispose()
                
                end_time = time.time()
                t.add_tool_call("db", "insert_cart_item", {"cart_id": cart_id, "product_id": product_id}, start_time, end_time, "SUCCESS", {"status": "inserted"})
                
                out = {
                    "success": True,
                    "action": "ADD_TO_CART",
                    "session_id": session_id,
                    "product_id": product_id,
                    "message": "Product successfully added to cart via direct DB write",
                    "details": {"cart_id": cart_id, "product_id": product_id, "status": "added"}
                }
                t.set_output(out)
                t.add_event("Added to cart successfully")
                return out
                
            except Exception as e:
                logger.error(f"CommerceEngine failed to add to cart: {e}")
                t.add_tool_call("db", "insert_cart_item", {"product_id": product_id}, start_time, time.time(), "FAILED", error=str(e))
                err_out = {
                    "success": False,
                    "error": {
                        "code": "COMMERCE_DB_ERROR",
                        "message": str(e)
                    }
                }
                t.set_output(err_out)
                t.set_error(e)
                return err_out
