from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ProductSchema(BaseModel):
    id: str
    slug: str
    name: str
    brand: str
    price: float
    stock: int
    is_active: bool
    specifications: Dict[str, Any]

class CartItemSchema(BaseModel):
    product_id: str
    quantity: int

class CartSchema(BaseModel):
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    items: List[CartItemSchema]
    
class CheckoutValidateRequest(BaseModel):
    address_id: Optional[str] = None

class BehavioralEventRequest(BaseModel):
    event_type: str
    session_id: str
    user_id: Optional[str] = None
    product_id: Optional[str] = None
    category_id: Optional[str] = None
    order_id: Optional[str] = None
    event_metadata: Dict[str, Any] = {}
