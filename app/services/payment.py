from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import ALLOWED_TRANSITIONS, PROMO_CODES, PaymentMethod, PaymentStatus
from app.models import Payment as PaymentORM
from app.repositories import PaymentRepository, TariffRepository
from app.schemas import PaymentCreate as PaymentCreateSchema
from app.schemas import PaymentRead as PaymentReadSchema
from app.schemas import WebhookEvent as WebhookEventSchema

def calculate_discount(price: int, promo_code: str | None) -> int:
    """Функция для подсчета скидки по промокоду"""
    if promo_code is None:
        return 0
    return (price * PROMO_CODES[promo_code] + 50) // 100

def build_schedule(amount: int, months: int) -> list[int]:
    """Функция для подсчета рассрочки платежа"""
    base, remainder = divmod(amount, months)
    return [base + 1 if i < remainder else base for i in range(months)]



class PaymentService:
    def __init__(
        self,
        session: AsyncSession,
        payments: PaymentRepository,
        tariffs: TariffRepository,
    ) -> None:
        self.session = session
        self.payments = payments
        self.tariffs = tariffs
        
        
    async def create(
        self, payload: PaymentCreateSchema, idempotency_key: str | None
    ) -> tuple[PaymentReadSchema, bool]:
        """Возвращает платёж и признак, был ли он создан этим запросом."""
        if idempotency_key:
            existing = await self.payments.get_by_idempotency_key(idempotency_key)
            if existing is not None:
                return PaymentReadSchema.model_validate(existing), False
        
        tariff = await self.tariffs.get_by_id(payload.tariff_id)
        if tariff is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тариф по платежу не найден")
        
        discount = calculate_discount(tariff.price, payload.promo_code)
        amount = tariff.price - discount
        
        schedule = None
        if payload.method == PaymentMethod.INSTALLMENT:
            schedule = build_schedule(amount, payload.installment_months)
            
        payment = PaymentORM(
            tariff_id=tariff.id,
            email=payload.email,
            method=payload.method,
            status=PaymentStatus.PENDING,
            amount=amount,
            discount=discount,
            installment_months=payload.installment_months,
            schedule=schedule,
            idempotency_key=idempotency_key or None,
        )
        
    
        try:
            await self.payments.create_payment(payment)
            await self.session.commit()
        except IntegrityError:
            # параллельный запрос с тем же ключом успел первым
            await self.session.rollback()
            if idempotency_key:
                existing = await self.payments.get_by_idempotency_key(idempotency_key)
                if existing is not None:
                    return PaymentReadSchema.model_validate(existing), False
            raise
        return PaymentReadSchema.model_validate(payment), True
    

    async def get(self, payment_id: int) -> PaymentReadSchema:
        payment = await self.payments.get_by_id(payment_id)
        if payment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Платеж не найден")
        return PaymentReadSchema.model_validate(payment)
    
    
    async def handle_webhook(self, event: WebhookEventSchema) -> None:
        payment = await self.payments.get_by_id(event.payment_id)
        if payment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Платеж не найден")
        if event.status not in ALLOWED_TRANSITIONS.get(payment.status, set()):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Запрещенный переход")
        payment.status = event.status
        await self.session.commit()