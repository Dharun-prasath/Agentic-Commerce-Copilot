"""Coupon service — server-side validation and discount calculation."""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.models.models import Coupon, CouponType
from app.schemas.commerce import CouponValidateRequest, CouponValidateResponse


class CouponService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def validate_coupon(self, data: CouponValidateRequest) -> CouponValidateResponse:
        result = await self.db.execute(
            select(Coupon).where(
                Coupon.code == data.code.upper(),
                Coupon.is_active == True,
            )
        )
        coupon = result.scalar_one_or_none()

        if not coupon:
            return CouponValidateResponse(
                valid=False, code=data.code, discount_amount=0,
                message="Coupon not found or inactive"
            )

        # Expiry check
        if coupon.expires_at and coupon.expires_at < datetime.now(timezone.utc):
            return CouponValidateResponse(
                valid=False, code=data.code, discount_amount=0,
                message="Coupon has expired"
            )

        # Usage limit check
        if coupon.max_uses is not None and coupon.used_count >= coupon.max_uses:
            return CouponValidateResponse(
                valid=False, code=data.code, discount_amount=0,
                message="Coupon usage limit reached"
            )

        # Minimum order amount check
        if data.subtotal < coupon.min_order_amount:
            return CouponValidateResponse(
                valid=False, code=data.code, discount_amount=0,
                message=f"Minimum order amount of ₹{coupon.min_order_amount:.0f} required"
            )

        # Calculate discount
        discount = self._calculate_discount(coupon, data.subtotal)

        return CouponValidateResponse(
            valid=True,
            code=coupon.code,
            discount_amount=round(discount, 2),
            message=f"Coupon applied! You save ₹{discount:.0f}",
            coupon_type=coupon.type.value,
            coupon_value=coupon.value,
        )

    def _calculate_discount(self, coupon: Coupon, subtotal: float) -> float:
        if coupon.type == CouponType.PERCENTAGE:
            discount = subtotal * (coupon.value / 100)
            if coupon.max_discount:
                discount = min(discount, coupon.max_discount)
            return discount
        else:  # FLAT
            return min(coupon.value, subtotal)

    async def get_coupon(self, code: str) -> Optional[Coupon]:
        result = await self.db.execute(
            select(Coupon).where(Coupon.code == code.upper(), Coupon.is_active == True)
        )
        return result.scalar_one_or_none()

    async def increment_usage(self, code: str) -> None:
        coupon = await self.get_coupon(code)
        if coupon:
            coupon.used_count += 1
