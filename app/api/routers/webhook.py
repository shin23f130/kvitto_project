from fastapi import APIRouter, Depends, HTTPException, status, Response

from app.api.dependencies import get_payment_service
from app.schemas import WebhookEvent as WebhookEventSchema
from app.services import PaymentService


router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/bank")
async def bank_webhook(
    event: WebhookEventSchema,
    response: Response,
    service: PaymentService = Depends(get_payment_service),
) -> dict[str, str]:
    try:
        await service.handle_webhook(event)
    except HTTPException as exc:
        if exc.status_code != status.HTTP_409_CONFLICT:
            raise
        response.status_code = status.HTTP_409_CONFLICT
        return {"error": "invalid_transition"}
    return {"result": "ok"}