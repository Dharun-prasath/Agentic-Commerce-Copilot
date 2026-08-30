"""Razorpay payment service — TEST MODE integration with graceful missing-credentials handling."""
import hmac
import hashlib
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.core.config import settings
from app.models.models import Payment, Order, PaymentStatus
from app.schemas.commerce import PaymentCreateResponse, PaymentVerifyRequest, PaymentVerifyResponse


class RazorpayNotConfiguredError(Exception):
    pass


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _get_client(self):
        """Returns a Razorpay client or raises a clear error if not configured."""
        if not settings.razorpay_configured:
            raise RazorpayNotConfiguredError(
                "Razorpay TEST MODE credentials are not configured. "
                "Please set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in your .env file. "
                "Get them from https://dashboard.razorpay.com → Settings → API Keys (Test Mode)."
            )
        import razorpay
        return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    async def create_razorpay_order(
        self,
        order: Order,
        user_name: str,
        user_email: str,
        user_phone: str,
    ) -> PaymentCreateResponse:
        try:
            client = self._get_client()
        except RazorpayNotConfiguredError as e:
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "RAZORPAY_NOT_CONFIGURED",
                    "message": str(e),
                    "setup_url": "https://dashboard.razorpay.com/app/website-app-settings/api-keys",
                }
            )

        amount_in_paise = int(round(order.total_amount * 100))
        razorpay_order = client.order.create({
            "amount": amount_in_paise,
            "currency": "INR",
            "receipt": order.order_number,
            "notes": {
                "order_id": order.id,
                "order_number": order.order_number,
            },
        })

        # Save payment record
        payment = Payment(
            order_id=order.id,
            razorpay_order_id=razorpay_order["id"],
            amount=order.total_amount,
            amount_in_paise=amount_in_paise,
            currency="INR",
            status=PaymentStatus.PENDING,
        )
        self.db.add(payment)
        await self.db.flush()

        return PaymentCreateResponse(
            razorpay_order_id=razorpay_order["id"],
            amount_in_paise=amount_in_paise,
            currency="INR",
            key_id=settings.RAZORPAY_KEY_ID,  # safe to expose — this is the PUBLIC key
            order_id=order.id,
            prefill={
                "name": user_name,
                "email": user_email,
                "contact": user_phone or "",
            },
        )

    async def verify_payment(self, data: PaymentVerifyRequest) -> PaymentVerifyResponse:
        """
        Critical: Verify Razorpay HMAC-SHA256 signature on the backend.
        A successful frontend callback alone NEVER marks an order as paid.
        """
        if not settings.razorpay_configured:
            raise HTTPException(
                status_code=503,
                detail={"error": "RAZORPAY_NOT_CONFIGURED", "message": "Razorpay not configured"}
            )

        # 1. Verify signature
        expected_signature = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode("utf-8"),
            f"{data.razorpay_order_id}|{data.razorpay_payment_id}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected_signature, data.razorpay_signature):
            # Mark payment as failed
            await self._mark_payment_failed(data.razorpay_order_id, "Signature verification failed")
            raise HTTPException(
                status_code=400,
                detail="Payment verification failed. Invalid signature."
            )

        # 2. Update payment record
        payment_result = await self.db.execute(
            select(Payment).where(Payment.razorpay_order_id == data.razorpay_order_id)
        )
        payment = payment_result.scalar_one_or_none()
        if not payment:
            raise HTTPException(status_code=404, detail="Payment record not found")

        payment.razorpay_payment_id = data.razorpay_payment_id
        payment.razorpay_signature = data.razorpay_signature
        payment.status = PaymentStatus.PAID

        # 3. Get order
        order_result = await self.db.execute(
            select(Order).where(Order.id == data.order_id)
        )
        order = order_result.scalar_one_or_none()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        await self.db.flush()

        return PaymentVerifyResponse(
            success=True,
            order_id=order.id,
            order_number=order.order_number,
            message="Payment verified successfully",
        )

    async def handle_webhook(self, payload: dict, signature: str) -> dict:
        """Handle Razorpay webhooks for asynchronous payment confirmation."""
        if not settings.RAZORPAY_WEBHOOK_SECRET:
            return {"status": "webhook_secret_not_configured"}
        try:
            import razorpay
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            client.utility.verify_webhook_signature(
                str(payload), signature, settings.RAZORPAY_WEBHOOK_SECRET
            )
        except Exception:
            raise HTTPException(status_code=400, detail="Webhook signature invalid")
        return {"status": "processed"}

    async def _mark_payment_failed(self, razorpay_order_id: str, reason: str) -> None:
        result = await self.db.execute(
            select(Payment).where(Payment.razorpay_order_id == razorpay_order_id)
        )
        payment = result.scalar_one_or_none()
        if payment:
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = reason
            order_result = await self.db.execute(
                select(Order).where(Order.id == payment.order_id)
            )
            order = order_result.scalar_one_or_none()
            if order:
                order.payment_status = PaymentStatus.FAILED
