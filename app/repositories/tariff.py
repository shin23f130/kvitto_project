from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Tariff as TariffORM

class TariffRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        
    async def get_all(self) -> Sequence[TariffORM]:
        stmt = select(TariffORM).order_by(TariffORM.id)
        result = await self.session.scalars(stmt)
        return result.all()
    
    async def get_by_id(self, tariff_id: int) -> TariffORM | None:
        return await self.session.get(TariffORM, tariff_id)