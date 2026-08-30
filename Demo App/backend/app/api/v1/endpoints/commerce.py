"""Address, Checkout, Payment, and Order API endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.models import User
from app.schemas.commerce import (
    AddressCreate, AddressUpdate, AddressOut,
    CheckoutCalculateRequest, CheckoutCalculateResponse,
    PaymentCreateRequest, PaymentCreateResponse,
    PaymentVerifyRequest, PaymentVerifyResponse,
    DeliveryOption, OrderOut
)
from app.services.wishlist_address_service import AddressService
from app.services.checkout_service import CheckoutService, DELIVERY_OPTIONS
from app.services.payment_service import PaymentService
from app.services.cart_service import CartService
from app.services.event_service import EventService
from app.schemas.commerce import EventCreate
from app.models.models import EventType

# ── Addresses ─────────────────────────────────────────────────────────────────

addresses_router = APIRouter(prefix="/addresses", tags=["addresses"])


@addresses_router.get("", response_model=List[AddressOut])
async def list_addresses(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await AddressService(db).list_addresses(user.id)


@addresses_router.post("", response_model=AddressOut, status_code=201)
async def create_address(data: AddressCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await AddressService(db).create_address(user.id, data)


@addresses_router.put("/{address_id}", response_model=AddressOut)
async def update_address(address_id: str, data: AddressUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await AddressService(db).update_address(user.id, address_id, data)


@addresses_router.delete("/{address_id}", status_code=204)
async def delete_address(address_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await AddressService(db).delete_address(user.id, address_id)


# ── Checkout ──────────────────────────────────────────────────────────────────

checkout_router = APIRouter(prefix="/checkout", tags=["checkout"])


@checkout_router.get("/delivery-options", response_model=List[DeliveryOption])
async def get_delivery_options():
    """Return available delivery options."""
    return CheckoutService(None).get_delivery_options()


@checkout_router.post("/calculate", response_model=CheckoutCalculateResponse)
async def calculate_checkout(
    data: CheckoutCalculateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Server-side checkout calculation — prices, tax, shipping, coupon discount."""
    svc = CheckoutService(db)
    result = await svc.calculate(user.id, data)
    # Track checkout started event (fire and forget)
    try:
        await EventService(db).track(EventCreate(
            event_type=EventType.CHECKOUT_STARTED,
            session_id="server",
            user_id=user.id,
            metadata={"delivery_method": data.delivery_method, "coupon_code": data.coupon_code},
        ))
    except Exception:
        pass
    return result


# ── Payments ──────────────────────────────────────────────────────────────────

payments_router = APIRouter(prefix="/payments", tags=["payments"])


@payments_router.post("/create", response_model=PaymentCreateResponse)
async def create_payment(
    data: PaymentCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a Razorpay order.
    Returns the Razorpay order ID and public key_id for the frontend.
    NEVER exposes RAZORPAY_KEY_SECRET.
    """
    checkout_svc = CheckoutService(db)
    order = await checkout_svc.create_pending_order(
        user_id=user.id,
        address_id=data.address_id,
        delivery_method=data.delivery_method,
        coupon_code=data.coupon_code,
        notes=data.notes,
    )
    payment_svc = PaymentService(db)
    response = await payment_svc.create_razorpay_order(
        order=order,
        user_name=user.name,
        user_email=user.email,
        user_phone=user.phone or "",
    )
    # Track payment started
    try:
        await EventService(db).track(EventCreate(
            event_type=EventType.PAYMENT_STARTED,
            session_id="server",
            user_id=user.id,
            order_id=order.id,
            metadata={"amount": order.total_amount},
        ))
    except Exception:
        pass
    return response


@payments_router.post("/verify", response_model=PaymentVerifyResponse)
async def verify_payment(
    data: PaymentVerifyRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Verify Razorpay payment signature on backend.
    On success, confirms the order and decrements stock.
    """
    payment_svc = PaymentService(db)
    result = await payment_svc.verify_payment(data)

    if result.success:
        # Confirm order
        checkout_svc = CheckoutService(db)
        await checkout_svc.confirm_order_paid(data.order_id)
        # Clear cart
        try:
            cart_svc = CartService(db)
            await cart_svc.clear_cart(user, None)
        except Exception:
            pass
        # Track events
        try:
            event_svc = EventService(db)
            await event_svc.track(EventCreate(
                event_type=EventType.PAYMENT_SUCCESS,
                session_id="server",
                user_id=user.id,
                order_id=data.order_id,
                metadata={"razorpay_payment_id": data.razorpay_payment_id},
            ))
            await event_svc.track(EventCreate(
                event_type=EventType.ORDER_CREATED,
                session_id="server",
                user_id=user.id,
                order_id=data.order_id,
                metadata={},
            ))
        except Exception:
            pass

    return result


@payments_router.post("/webhook")
async def razorpay_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle Razorpay webhook events."""
    payload = await request.json()
    signature = request.headers.get("X-Razorpay-Signature", "")
    payment_svc = PaymentService(db)
    result = await payment_svc.handle_webhook(payload, signature)
    return JSONResponse(content=result)


# ── Orders ────────────────────────────────────────────────────────────────────

orders_router = APIRouter(prefix="/orders", tags=["orders"])


@orders_router.get("", response_model=List[OrderOut])
async def list_orders(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await CheckoutService(db).list_orders(user.id)


@orders_router.get("/{order_id}", response_model=OrderOut)
async def get_order(order_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await CheckoutService(db).get_order(order_id, user.id)
