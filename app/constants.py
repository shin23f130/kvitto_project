from enum import StrEnum

DEFAULT_TARIFFS = [ #цены в копейках
    {"title": "basic", "price": 990_000},
    {"title": "standard", "price": 1_990_000},
    {"title": "premium", "price": 2_990_000}
]

PROMO_CODES = {"KVITTO10": 10}

class PaymentMethod(StrEnum):
    CARD = "card"
    SBP = "sbp"
    INSTALLMENT = "installment"
    
class PaymentStatus(StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"
    

ALLOWED_TRANSITIONS = {
    PaymentStatus.PENDING: {PaymentStatus.SUCCEEDED, PaymentStatus.FAILED},
    PaymentStatus.SUCCEEDED: {PaymentStatus.REFUNDED}
}