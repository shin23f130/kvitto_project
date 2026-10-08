from fastapi import APIRouter, Depends

from app.api.dependencies import get_tariff_service
from app.schemas import TariffRead as TariffReadSchema
from app.services import TariffService

router = APIRouter(prefix="/tariffs", tags=["tariffs"])


@router.get("", response_model=list[TariffReadSchema])
async def get_tariffs(
    service: TariffService = Depends(get_tariff_service),
) -> list[TariffReadSchema]:
    return await service.get_all()