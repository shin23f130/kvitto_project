from app.repositories import TariffRepository
from app.schemas import TariffRead as TariffReadSchema


class TariffService:
    def __init__(self, tariffs: TariffRepository) -> None:
        self.tariffs = tariffs
        
    async def get_all(self) -> list[TariffReadSchema]:
        tariffs = await self.tariffs.get_all()
        return [TariffReadSchema.model_validate(tariff) for tariff in tariffs] 