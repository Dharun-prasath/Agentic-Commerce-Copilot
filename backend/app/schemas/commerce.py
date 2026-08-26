"""Pydantic schemas — Cart, Coupon, Checkout, Orders, Payments, Events, Address"""
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, field_validator
from app.models.models import OrderStatus, PaymentStatus, EventType


# ── Address ──────────────────────────────────────────────────────────────────

class AddressCreate(BaseModel):
    name: str
    phone: str
    line1: str
    line2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country: str = "India"
    is_default: bool = False


class AddressUpdate(AddressCreate):
    pass


class AddressOut(AddressCreate):
    id: str
    model_config = {"from_attributes": True}


# ── Cart ──────────────────────────────────────────────────────────────────────

class CartItemAdd(BaseModel):
    product_id: str
    quantity: int = 1

    @field_validator("quantity")
    @classmethod
    def qty_positive(cls, v):
        if v < 1:
            raise ValueError("Quantity must be at least 1")
        return v


class CartItemUpdate(BaseModel):
    quantity: int

    @field_validator("quantity")
    @classmethod
    def qty_positive(cls, v):
        if v < 1:
            raise ValueError("Quantity must be at least 1")
        return v


class CartItemOut(BaseModel):
    id: str
    product_id: str
    product_name: str
    product_brand: str
    product_thumbnail: Optional[str]
    product_slug: str
    unit_price: float
    original_price: float
    quantity: int
    subtotal: float
    stock: int

    model_config = {"from_attributes": True}


class CartOut(BaseModel):
    id: str
    items: List[CartItemOut]
    coupon_code: Optional[str]
    item_count: int
    subtotal: float

    model_config = {"from_attributes": True}


# ── Coupon ───────────────────────────────────────────────────────────────────

class CouponValidateRequest(BaseModel):
    code: str
    subtotal: float


class CouponValidateResponse(BaseModel):
    valid: bool
    code: str
    discount_amount: float
    message: str
    coupon_type: Optional[str] = None
    coupon_value: Optional[float] = None


# ── Checkout ──────────────────────────────────────────────────────────────────

class DeliveryOption(BaseModel):
    id: str
    name: str
    description: str
    price: float
    estimated_days: int


class CheckoutCalculateRequest(BaseModel):
    address_id: str
    delivery_method: str  # "STANDARD" | "EXPRESS" | "OVERNIGHT"
    coupon_code: Optional[str] = None


class CheckoutCalculateResponse(BaseModel):
    subtotal: float
    coupon_discount: float
    coupon_code: Optional[str]
    tax_rate: float
    tax_amount: float
    shipping_charge: float
    total_amount: float
    delivery_method: str
    delivery_days: int
    items: List[CartItemOut]


# ── Payment ───────────────────────────────────────────────────────────────────

class PaymentCreateRequest(BaseModel):
    address_id: str
    delivery_method: str
    coupon_code: Optional[str] = None
    notes: Optional[str] = None


class PaymentCreateResponse(BaseModel):
    razorpay_order_id: str
    amount_in_paise: int
    currency: str
    key_id: str
    order_id: str  # our internal order id
    prefill: Dict[str, Any]


class PaymentVerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    order_id: str


class PaymentVerifyResponse(BaseModel):
    success: bool
    order_id: str
    order_number: str
    message: str


# ── Order ─────────────────────────────────────────────────────────────────────

class OrderItemOut(BaseModel):
    id: str
    product_id: Optional[str]
    product_name: str
    product_brand: str
    product_thumbnail: Optional[str]
    unit_price: float
    original_price: float
    quantity: int
    total_price: float

    model_config = {"from_attributes": True}


class OrderOut(BaseModel):
    id: str
    order_number: str
    status: OrderStatus
    payment_status: PaymentStatus
    shipping_name: str
    shipping_phone: str
    shipping_line1: str
    shipping_line2: Optional[str]
    shipping_city: str
    shipping_state: str
    shipping_postal_code: str
    shipping_country: str
    delivery_method: str
    delivery_days: int
    subtotal: float
    coupon_code: Optional[str]
    coupon_discount: float
    tax_amount: float
    shipping_charge: float
    total_amount: float
    items: List[OrderItemOut]
    created_at: str

    model_config = {"from_attributes": True}


# ── Events ────────────────────────────────────────────────────────────────────

class EventCreate(BaseModel):
    event_type: EventType
    session_id: str
    user_id: Optional[str] = None
    product_id: Optional[str] = None
    category_id: Optional[str] = None
    order_id: Optional[str] = None
    metadata: Dict[str, Any] = {}


class EventOut(BaseModel):
    id: str
    event_type: str
    session_id: str
    user_id: Optional[str]
    product_id: Optional[str]
    category_id: Optional[str]
    order_id: Optional[str]
    metadata: Dict[str, Any]
    created_at: str

    model_config = {"from_attributes": True}


# ── Wishlist ──────────────────────────────────────────────────────────────────

class WishlistItemAdd(BaseModel):
    product_id: str


class WishlistItemOut(BaseModel):
    id: str
    product_id: str
    product_name: str
    product_brand: str
    product_thumbnail: Optional[str]
    product_slug: str
    price: float
    original_price: float
    discount_percentage: float
    rating: float
    stock: int

    model_config = {"from_attributes": True}


class WishlistOut(BaseModel):
    id: str
    items: List[WishlistItemOut]
    item_count: int

    model_config = {"from_attributes": True}
