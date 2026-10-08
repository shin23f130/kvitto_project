import pytest
from httpx import AsyncClient

PRICES = {"basic": 990_000, "standard": 1_990_000, "premium": 2_990_000}


async def get_tariff_id(client: AsyncClient, title: str) -> int:
    response = await client.get("/tariffs")
    return next(item["id"] for item in response.json() if item["title"] == title)


async def create_payment(client: AsyncClient, title: str = "standard", headers=None, **fields):
    body = {
        "tariff_id": await get_tariff_id(client, title),
        "email": "user@example.com",
        "method": "card",
        **fields,
    }
    return await client.post("/payments", json=body, headers=headers)


async def test_tariffs_are_seeded(client: AsyncClient):
    response = await client.get("/tariffs")

    assert response.status_code == 200
    assert {item["title"]: item["price"] for item in response.json()} == PRICES


async def test_amount_without_promo_code(client: AsyncClient):
    response = await create_payment(client)

    assert response.status_code == 201
    payment = response.json()
    assert payment["amount"] == 1_990_000
    assert payment["discount"] == 0
    assert payment["status"] == "pending"
    assert payment["schedule"] is None
    assert payment["installment_months"] is None


@pytest.mark.parametrize("promo_code", ["KVITTO10", "kvitto10", "Kvitto10"])
async def test_amount_with_promo_code_ignores_case(client: AsyncClient, promo_code: str):
    response = await create_payment(client, promo_code=promo_code)

    assert response.status_code == 201
    payment = response.json()
    assert payment["discount"] == 199_000
    assert payment["amount"] == 1_791_000


async def test_unknown_promo_code_returns_422(client: AsyncClient):
    response = await create_payment(client, promo_code="NOPE")

    assert response.status_code == 422


async def test_schedule_matches_example_from_task(client: AsyncClient):
    response = await create_payment(client, method="installment", installment_months=3)

    assert response.json()["schedule"] == [663_334, 663_333, 663_333]


@pytest.mark.parametrize("months", [3, 6, 12])
@pytest.mark.parametrize("title", ["basic", "standard", "premium"])
@pytest.mark.parametrize("promo_code", [None, "KVITTO10"])
async def test_schedule_sum_equals_amount(
    client: AsyncClient, months: int, title: str, promo_code: str | None
):
    fields = {"method": "installment", "installment_months": months}
    if promo_code:
        fields["promo_code"] = promo_code

    response = await create_payment(client, title, **fields)

    assert response.status_code == 201
    payment = response.json()
    schedule = payment["schedule"]
    assert len(schedule) == months
    assert sum(schedule) == payment["amount"]
    assert all(isinstance(part, int) for part in schedule)
    # лишние копейки достаются первым платежам
    assert schedule == sorted(schedule, reverse=True)
    assert max(schedule) - min(schedule) <= 1


async def test_installment_requires_months(client: AsyncClient):
    response = await create_payment(client, method="installment")

    assert response.status_code == 422


async def test_same_idempotency_key_does_not_create_second_payment(client: AsyncClient):
    headers = {"Idempotency-Key": "order-42"}

    first = await create_payment(client, headers=headers)
    second = await create_payment(client, headers=headers)

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json() == first.json()

    third = await create_payment(client)
    assert third.json()["id"] == first.json()["id"] + 1


async def test_allowed_transitions_change_status(client: AsyncClient):
    payment_id = (await create_payment(client)).json()["id"]

    for status in ("succeeded", "refunded"):
        response = await client.post(
            "/webhooks/bank", json={"payment_id": payment_id, "status": status}
        )
        assert response.status_code == 200
        assert response.json() == {"result": "ok"}
        assert (await client.get(f"/payments/{payment_id}")).json()["status"] == status


async def test_forbidden_transition_returns_409_and_keeps_status(client: AsyncClient):
    payment_id = (await create_payment(client)).json()["id"]
    await client.post("/webhooks/bank", json={"payment_id": payment_id, "status": "failed"})

    response = await client.post(
        "/webhooks/bank", json={"payment_id": payment_id, "status": "succeeded"}
    )

    assert response.status_code == 409
    assert response.json() == {"error": "invalid_transition"}
    assert (await client.get(f"/payments/{payment_id}")).json()["status"] == "failed"


async def test_pending_to_refunded_is_forbidden(client: AsyncClient):
    payment_id = (await create_payment(client)).json()["id"]

    response = await client.post(
        "/webhooks/bank", json={"payment_id": payment_id, "status": "refunded"}
    )

    assert response.status_code == 409
    assert (await client.get(f"/payments/{payment_id}")).json()["status"] == "pending"


async def test_missing_payment_returns_404(client: AsyncClient):
    assert (await client.get("/payments/999999")).status_code == 404

    response = await client.post(
        "/webhooks/bank", json={"payment_id": 999999, "status": "succeeded"}
    )
    assert response.status_code == 404
