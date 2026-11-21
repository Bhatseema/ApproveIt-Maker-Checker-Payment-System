from decimal import Decimal, InvalidOperation
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional

class PaymentCreate(BaseModel):
    beneficiary_name: str = Field(min_length=1, max_length=200)
    beneficiary_id: str = Field(min_length=1, max_length=100)
    amount: Decimal = Field(gt=0)
    purpose: str = Field(min_length=1, max_length=500)

    @field_validator("beneficiary_name", "beneficiary_id", "purpose")
    @classmethod
    def validate_nonblank_text(cls, value: str):
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank")
        return value

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: Decimal):
        try:
            value = Decimal(value)
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError("Amount must be a valid number")
        if not value.is_finite():
            raise ValueError("Amount must be a finite number")
        if value <= 0:
            raise ValueError("Amount must be greater than zero")
        if value.as_tuple().exponent < -2:
            raise ValueError("Amount can have at most two decimal places")
        return value

class PaymentUpdate(PaymentCreate):
    pass

class RejectRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str):
        value = value.strip()
        if not value:
            raise ValueError("Rejection reason is required")
        return value

class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    maker_id: str
    beneficiary_name: str
    beneficiary_id: str
    amount: Decimal
    purpose: str
    status: str
    created_at: str
    submitted_at: Optional[str] = None
    approvals_received: int
    approvals_required: int

class MessageOut(BaseModel):
    payment_id: int
    status: str
    message: str
