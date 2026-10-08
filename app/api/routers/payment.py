from fastapi import APIRouter, Depends, Header, Response, status

from app.api.dependencies import get_payment_service
from app.schemas import PaymentCreate as PaymentCreateSchema
from app.schemas import PaymentRead as PaymentReadSchema
from app.services import PaymentService

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("", response_model=PaymentReadSchema, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payload: PaymentCreateSchema,
    response: Response,
    idempotency_key: str | None = Header(default=None),
    service: PaymentService = Depends(get_payment_service),
) -> PaymentReadSchema:
    payment, created = await service.create(payload, idempotency_key)
    if not created:
        response.status_code = status.HTTP_200_OK
    return payment


@router.get("/{payment_id}", response_model=PaymentReadSchema)
async def get_payment(
    payment_id: int,
    service: PaymentService = Depends(get_payment_service),
) -> PaymentReadSchema:
    return await service.get(payment_id)
