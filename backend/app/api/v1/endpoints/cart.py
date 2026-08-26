"""Cart API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import get_current_user_optional
from app.schemas.commerce import CartItemAdd, CartItemUpdate, CartOut, CouponValidateRequest, CouponValidateResponse
from app.services.cart_service import CartService
from app.services.coupon_service import CouponService
from app.models.models import User

router = APIRouter(prefix="/cart", tags=["cart"])


def _get_session(x_session_id: Optional[str] = Header(None)) -> Optional[str]:
    return x_session_id


@router.get("", response_model=CartOut)
async def get_cart(
    user: Optional[User] = Depends(get_current_user_optional),
    session_id: Optional[str] = Depends(_get_session),
    db: AsyncSession = Depends(get_db),
):
    """Get the current cart (supports both authenticated and anonymous users)."""
    return await CartService(db).get_cart(user, session_id)


@router.post("/items", response_model=CartOut, status_code=201)
async def add_item(
    data: CartItemAdd,
    user: Optional[User] = Depends(get_current_user_optional),
    session_id: Optional[str] = Depends(_get_session),
    db: AsyncSession = Depends(get_db),
):
    """Add a product to the cart."""
    return await CartService(db).add_item(user, session_id, data)


@router.patch("/items/{item_id}", response_model=CartOut)
async def update_item(
    item_id: str,
    data: CartItemUpdate,
    user: Optional[User] = Depends(get_current_user_optional),
    session_id: Optional[str] = Depends(_get_session),
    db: AsyncSession = Depends(get_db),
):
    """Update quantity of a cart item."""
    return await CartService(db).update_item(user, session_id, item_id, data)


@router.delete("/items/{item_id}", response_model=CartOut)
async def remove_item(
    item_id: str,
    user: Optional[User] = Depends(get_current_user_optional),
    session_id: Optional[str] = Depends(_get_session),
    db: AsyncSession = Depends(get_db),
):
    """Remove a product from the cart."""
    return await CartService(db).remove_item(user, session_id, item_id)


@router.post("/coupon", response_model=CouponValidateResponse)
async def validate_coupon(
    data: CouponValidateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Validate a coupon code and get discount amount (server-side)."""
    return await CouponService(db).validate_coupon(data)


@router.delete("", status_code=204)
async def clear_cart(
    user: Optional[User] = Depends(get_current_user_optional),
    session_id: Optional[str] = Depends(_get_session),
    db: AsyncSession = Depends(get_db),
):
    """Clear the entire cart."""
    await CartService(db).clear_cart(user, session_id)
