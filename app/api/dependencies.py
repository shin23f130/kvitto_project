from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.repositories import PaymentRepository, TariffRepository
from app.services import PaymentService, TariffService



def get_tariff_service(session: AsyncSession = Depends(get_db)) -> TariffService:
    return TariffService(TariffRepository(session))

def get_payment_service(session: AsyncSession = Depends(get_db)) -> PaymentService:
    return PaymentService(
        session=session,
        payments=PaymentRepository(session),
        tariffs=TariffRepository(session),
    )