import base64
import hashlib
import hmac
from uuid import uuid4
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.config import settings
from app.database import get_db_session
from app.models.entities import PaymentRecord, PaymentStatus, User
from app.schemas.billing import (
    CreatePaymentOrderRequest,
    CreatePaymentOrderResponse,
    PaymentRecordRead,
    VerifyPaymentRequest,
)
from app.services.auth import get_current_user
from app.services.catalog import get_tier_by_code

router = APIRouter(prefix="/payments", tags=["payments"])


def _require_razorpay():
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment gateway is not configured yet.",
        )


async def _create_razorpay_order(amount_paise: int, receipt: str) -> dict:
    creds = f"{settings.RAZORPAY_KEY_ID}:{settings.RAZORPAY_KEY_SECRET}".encode()
    auth_header = base64.b64encode(creds).decode()
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            "https://api.razorpay.com/v1/orders",
            headers={
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/json",
            },
            json={
                "amount": amount_paise,
                "currency": settings.PAYMENT_CURRENCY,
                "receipt": receipt,
                "payment_capture": 1,
            },
        )
        response.raise_for_status()
        return response.json()


@router.post("/order", response_model=CreatePaymentOrderResponse)
async def create_payment_order(
    payload: CreatePaymentOrderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    _require_razorpay()
    tier = get_tier_by_code(payload.plan_code)
    if not tier:
        raise HTTPException(status_code=404, detail="Selected plan does not exist.")
    if tier["is_enterprise"] or tier["price_inr"] <= 0:
        raise HTTPException(status_code=400, detail="This plan is not payable through checkout.")

    amount_paise = tier["price_inr"] * 100
    receipt = f"{payload.plan_code}-{uuid4().hex[:16]}"
    order = await _create_razorpay_order(amount_paise, receipt)

    payment_record = PaymentRecord(
        user_id=current_user.id,
        plan_code=tier["code"],
        amount_inr=tier["price_inr"],
        currency=settings.PAYMENT_CURRENCY,
        status=PaymentStatus.CREATED,
        razorpay_order_id=order["id"],
    )
    db.add(payment_record)
    await db.commit()
    await db.refresh(payment_record)

    return CreatePaymentOrderResponse(
        payment_record_id=payment_record.id,
        order_id=order["id"],
        amount=order["amount"],
        currency=order["currency"],
        key_id=settings.RAZORPAY_KEY_ID,
        plan_code=tier["code"],
        plan_name=tier["name"],
        merchant_name=settings.APP_NAME,
        description=f"{tier['name']} subscription",
    )


@router.post("/verify", response_model=PaymentRecordRead)
async def verify_payment(
    payload: VerifyPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    _require_razorpay()
    result = await db.execute(
        select(PaymentRecord).where(
            PaymentRecord.id == payload.payment_record_id,
            PaymentRecord.user_id == current_user.id,
        )
    )
    payment_record = result.scalars().first()
    if not payment_record:
        raise HTTPException(status_code=404, detail="Payment record not found.")

    signed_payload = f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}".encode()
    expected_signature = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, payload.razorpay_signature):
        payment_record.status = PaymentStatus.FAILED
        db.add(payment_record)
        await db.commit()
        raise HTTPException(status_code=400, detail="Payment signature verification failed.")

    payment_record.status = PaymentStatus.PAID
    payment_record.razorpay_order_id = payload.razorpay_order_id
    payment_record.razorpay_payment_id = payload.razorpay_payment_id
    payment_record.razorpay_signature = payload.razorpay_signature
    db.add(payment_record)
    await db.commit()
    await db.refresh(payment_record)
    return payment_record
