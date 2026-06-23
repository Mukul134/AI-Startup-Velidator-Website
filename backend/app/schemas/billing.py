from datetime import datetime
from typing import Literal, Optional
from uuid import UUID
from pydantic import BaseModel


class PricingTierRead(BaseModel):
    code: str
    name: str
    price_inr: int
    period: str
    description: str
    features: list[str]
    cta: str
    popular: bool
    is_enterprise: bool


class PublicOverviewRead(BaseModel):
    total_projects: int
    completed_reports: int
    active_founders: int
    average_score: int


class CreatePaymentOrderRequest(BaseModel):
    plan_code: str


class CreatePaymentOrderResponse(BaseModel):
    payment_record_id: UUID
    order_id: str
    amount: int
    currency: str
    key_id: str
    plan_code: str
    plan_name: str
    merchant_name: str
    description: str


class VerifyPaymentRequest(BaseModel):
    payment_record_id: UUID
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class PaymentRecordRead(BaseModel):
    id: UUID
    user_id: UUID
    plan_code: str
    amount_inr: int
    currency: str
    status: Literal["created", "paid", "failed"]
    razorpay_order_id: str
    razorpay_payment_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
