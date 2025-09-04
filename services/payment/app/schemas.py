from pydantic import BaseModel
import uuid
from typing import Optional
from datetime import datetime

class PaymentRequest(BaseModel):
    booking_id: uuid.UUID
    amount: float
    phone_number: str

class PaymentResponse(BaseModel):
    payment_id: str
    message: str
    requires_verification: bool

class PaymentReceipt(BaseModel):
    payment_id: str
    amount: float
    status: str
    created_at: datetime
    phone_number: str 