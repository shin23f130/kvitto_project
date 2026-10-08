from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator, model_validator

from app.constants import PROMO_CODES, PaymentMethod, PaymentStatus

class PaymentCreate(BaseModel):
    tariff_id: int
    email: EmailStr
    method: PaymentMethod
    installment_months: Literal[3, 6, 12] | None = None
    promo_code: str | None = None
    
    
    @field_validator("promo_code")
    @classmethod
    def normalize_promo_code(cls, value: str | None) -> str | None:
        if value is None:
            return None
        code = value.strip().upper()
        if code not in PROMO_CODES:
            raise ValueError("unknown promo code")
        return code
    
    @model_validator(mode="after")
    def check_installment_months(self) -> Self:
        if self.method == PaymentMethod.INSTALLMENT and self.installment_months is None:
            raise ValueError("installment_months is required for installment")
        if self.method != PaymentMethod.INSTALLMENT and self.installment_months is not None:
            raise ValueError("installment_months is allowed only for installment")
        return self
    
    
class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: PaymentStatus
    tariff_id: int
    amount: int
    discount: int
    method: PaymentMethod
    installment_months: int | None
    schedule: list[int] | None
    email: EmailStr
    created_at: datetime
    
class WebhookEvent(BaseModel):
    payment_id: int
    status: PaymentStatus