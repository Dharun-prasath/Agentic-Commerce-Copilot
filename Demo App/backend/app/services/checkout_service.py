"""Checkout + Order service — server-side price calculation and order creation."""
import random
import string
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from app.models.models import (
    Cart, CartItem, Product, Address, Order, OrderItem, Payment,
    OrderStatus, PaymentStatus, Coupon
)
from app.schemas.commerce import (
    CheckoutCalculateRequest, CheckoutCalculateResponse,
    CartItemOut, OrderOut, OrderItemOut, DeliveryOption
)
from app.services.coupon_service import CouponService
from app.core.config import settings


DELIVERY_OPTIONS = {
    "STANDARD": {"name": "Standard Delivery", "description": "5-7 business days", "price": 0.0, "days": 6},
    "EXPRESS":  {"name": "Express Delivery",  "description": "2-3 business days", "price": 249.0, "days": 2},
    "OVERNIGHT":{"name": "Overnight Delivery","description": "Next business day",  "price": 499.0, "days": 1},
}
FREE_SHIPPING_THRESHOLD = 50_000.0


class CheckoutService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.coupon_svc = CouponService(db)

    def get_delivery_options(self) -> List[DeliveryOption]:
        return [
            DeliveryOption(
                id=k,
                name=v["name"],
                description=v["description"],
                price=v["price"],
                estimated_days=v["days"],
            )
            for k, v in DELIVERY_OPTIONS.items()
        ]

    async def calculate(
        self, user_id: str, data: CheckoutCalculateRequest
    ) -> CheckoutCalculateResponse:
        # Load cart
        cart = await self._load_user_cart(user_id)
        if not cart or not cart.items:
            raise HTTPException(status_code=400, detail="Cart is empty")

        # Load address
        await self._validate_address(user_id, data.address_id)

        # Load delivery option
        delivery = DELIVERY_OPTIONS.get(data.delivery_method)
        if not delivery:
            raise HTTPException(status_code=400, detail="Invalid delivery method")

        # Calculate subtotal from DB prices (never trust frontend)
        subtotal = sum(item.product.price * item.quantity for item in cart.items if item.product)

        # Coupon discount
        coupon_discount = 0.0
        if data.coupon_code:
            from app.schemas.commerce import CouponValidateRequest
            result = await self.coupon_svc.validate_coupon(
                CouponValidateRequest(code=data.coupon_code, subtotal=subtotal)
            )
            if result.valid:
                coupon_discount = result.discount_amount

        # Shipping
        after_discount = subtotal - coupon_discount
        shipping_charge = 0.0 if subtotal >= FREE_SHIPPING_THRESHOLD else delivery["price"]

        # Tax (18% GST on subtotal after discount)
        tax_amount = round((after_discount) * settings.TAX_RATE, 2)

        total = round(after_discount + tax_amount + shipping_charge, 2)

        # Cart items for response
        cart_items = []
        for ci in cart.items:
            p = ci.product
            if p:
                thumbnail = p.thumbnail or (p.images[0].url if p.images else None)
                cart_items.append(CartItemOut(
                    id=ci.id, product_id=p.id, product_name=p.name,
                    product_brand=p.brand, product_thumbnail=thumbnail,
                    product_slug=p.slug, unit_price=p.price,
                    original_price=p.original_price, quantity=ci.quantity,
                    subtotal=round(p.price * ci.quantity, 2), stock=p.stock,
                ))

        return CheckoutCalculateResponse(
            subtotal=round(subtotal, 2),
            coupon_discount=round(coupon_discount, 2),
            coupon_code=data.coupon_code if coupon_discount > 0 else None,
            tax_rate=settings.TAX_RATE,
            tax_amount=tax_amount,
            shipping_charge=shipping_charge,
            total_amount=total,
            delivery_method=data.delivery_method,
            delivery_days=delivery["days"],
            items=cart_items,
        )

    async def create_pending_order(
        self,
        user_id: str,
        address_id: str,
        delivery_method: str,
        coupon_code: Optional[str],
        notes: Optional[str],
    ) -> Order:
        """Creates a PENDING order before Razorpay payment is initiated."""
        calc = await self.calculate(
            user_id,
            CheckoutCalculateRequest(
                address_id=address_id,
                delivery_method=delivery_method,
                coupon_code=coupon_code,
            ),
        )
        address = await self._get_address(user_id, address_id)
        order_number = self._generate_order_number()
        delivery = DELIVERY_OPTIONS[delivery_method]

        order = Order(
            order_number=order_number,
            user_id=user_id,
            status=OrderStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            shipping_name=address.name,
            shipping_phone=address.phone,
            shipping_line1=address.line1,
            shipping_line2=address.line2,
            shipping_city=address.city,
            shipping_state=address.state,
            shipping_postal_code=address.postal_code,
            shipping_country=address.country,
            delivery_method=delivery_method,
            delivery_days=delivery["days"],
            subtotal=calc.subtotal,
            coupon_code=calc.coupon_code,
            coupon_discount=calc.coupon_discount,
            tax_amount=calc.tax_amount,
            shipping_charge=calc.shipping_charge,
            total_amount=calc.total_amount,
            notes=notes,
        )
        self.db.add(order)
        await self.db.flush()

        # Create order items (snapshot product data)
        cart = await self._load_user_cart(user_id)
        for ci in cart.items:
            p = ci.product
            if p:
                thumbnail = p.thumbnail or (p.images[0].url if p.images else None)
                self.db.add(OrderItem(
                    order_id=order.id,
                    product_id=p.id,
                    product_name=p.name,
                    product_brand=p.brand,
                    product_thumbnail=thumbnail,
                    unit_price=p.price,
                    original_price=p.original_price,
                    quantity=ci.quantity,
                    total_price=round(p.price * ci.quantity, 2),
                ))

        await self.db.flush()
        await self.db.refresh(order)
        return order

    async def confirm_order_paid(self, order_id: str) -> Order:
        """Called after successful Razorpay signature verification."""
        result = await self.db.execute(
            select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        order.status = OrderStatus.CONFIRMED
        order.payment_status = PaymentStatus.PAID
        # Decrement stock
        for item in order.items:
            prod_result = await self.db.execute(select(Product).where(Product.id == item.product_id))
            product = prod_result.scalar_one_or_none()
            if product:
                product.stock = max(0, product.stock - item.quantity)
        await self.db.flush()
        return order

    async def get_order(self, order_id: str, user_id: str) -> OrderOut:
        result = await self.db.execute(
            select(Order).options(selectinload(Order.items))
            .where(Order.id == order_id, Order.user_id == user_id)
        )
        order = result.scalar_one_or_none()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return self._serialize_order(order)

    async def list_orders(self, user_id: str) -> List[OrderOut]:
        result = await self.db.execute(
            select(Order).options(selectinload(Order.items))
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
        )
        return [self._serialize_order(o) for o in result.scalars()]

    # ── Helpers ────────────────────────────────────────────────────────────────

    async def _load_user_cart(self, user_id: str) -> Optional[Cart]:
        result = await self.db.execute(
            select(Cart)
            .options(selectinload(Cart.items).selectinload(CartItem.product).selectinload(Product.images))
            .where(Cart.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def _validate_address(self, user_id: str, address_id: str) -> None:
        address = await self._get_address(user_id, address_id)
        if not address:
            raise HTTPException(status_code=404, detail="Address not found")

    async def _get_address(self, user_id: str, address_id: str) -> Address:
        result = await self.db.execute(
            select(Address).where(Address.id == address_id, Address.user_id == user_id)
        )
        address = result.scalar_one_or_none()
        if not address:
            raise HTTPException(status_code=404, detail="Address not found")
        return address

    def _generate_order_number(self) -> str:
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        return f"ACC-{suffix}"

    def _serialize_order(self, order: Order) -> OrderOut:
        items = [
            OrderItemOut(
                id=i.id, product_id=i.product_id,
                product_name=i.product_name, product_brand=i.product_brand,
                product_thumbnail=i.product_thumbnail,
                unit_price=i.unit_price, original_price=i.original_price,
                quantity=i.quantity, total_price=i.total_price,
            )
            for i in (order.items or [])
        ]
        return OrderOut(
            id=order.id,
            order_number=order.order_number,
            status=order.status,
            payment_status=order.payment_status,
            shipping_name=order.shipping_name,
            shipping_phone=order.shipping_phone,
            shipping_line1=order.shipping_line1,
            shipping_line2=order.shipping_line2,
            shipping_city=order.shipping_city,
            shipping_state=order.shipping_state,
            shipping_postal_code=order.shipping_postal_code,
            shipping_country=order.shipping_country,
            delivery_method=order.delivery_method,
            delivery_days=order.delivery_days,
            subtotal=order.subtotal,
            coupon_code=order.coupon_code,
            coupon_discount=order.coupon_discount,
            tax_amount=order.tax_amount,
            shipping_charge=order.shipping_charge,
            total_amount=order.total_amount,
            items=items,
            created_at=order.created_at.isoformat() if order.created_at else "",
        )
