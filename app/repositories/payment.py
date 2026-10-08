from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Payment as PaymentORM


class PaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        
    async def get_by_id(self, payment_id: int) -> PaymentORM | None:
        return await self.session.get(PaymentORM, payment_id)
    
    async def get_by_idempotency_key(self, key: str) -> PaymentORM | None:
        return await self.session.scalar(
            select(PaymentORM).where(PaymentORM.idempotency_key == key)
        )
        
    async def create_payment(self, payment: PaymentORM) -> PaymentORM:
        self.session.add(payment)
        await self.session.flush()
        return payment
