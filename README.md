# Kvitto payments

API платежей на FastAPI: тарифы, создание платежа со скидкой и рассрочкой,
уведомление от банка о смене статуса.

Стек: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2 (async), PostgreSQL, pytest + httpx.

## Запуск

Нужен Docker с Docker Compose.

```bash
docker compose up --build
```

Поднимаются PostgreSQL и приложение. При старте создаются таблицы и три тарифа.

- API: http://localhost:8000
- Swagger: http://localhost:8000/docs

### Запуск без контейнера для приложения

Нужен [uv](https://docs.astral.sh/uv/). База остаётся в Docker.

```bash
docker compose up -d db
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

Адрес базы берётся из переменной `DATABASE_URL`; значение по умолчанию —
`postgresql+asyncpg://app:app@127.0.0.1:5433/app` — совпадает с настройками
в `docker-compose.yml`.

## Тесты

```bash
uv sync
uv run pytest
```

Тесты работают на SQLite в памяти, Docker для них не нужен.

## Примеры запросов

Список тарифов:

```bash
curl http://localhost:8000/tariffs
```

Платёж в рассрочку с промокодом (`tariff_id` возьми из ответа выше, `2` — standard):

```bash
curl -X POST http://localhost:8000/payments \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: order-1" \
  -d '{"tariff_id": 2, "email": "user@example.com", "method": "installment", "installment_months": 3, "promo_code": "kvitto10"}'
```

В ответе `amount` равен `1791000`, `discount` — `199000`, `schedule` —
`[597000, 597000, 597000]`. Повтор запроса с тем же `Idempotency-Key`
вернёт тот же платёж с кодом 200.

Получить платёж:

```bash
curl http://localhost:8000/payments/1
```

Уведомление от банка:

```bash
curl -X POST http://localhost:8000/webhooks/bank \
  -H "Content-Type: application/json" \
  -d '{"payment_id": 1, "status": "succeeded"}'
```

Успех — `{"result": "ok"}`. Запрещённый переход (например, повторный `succeeded`)
вернёт 409 `{"error": "invalid_transition"}`, статус платежа не изменится.

## Решения

- Все суммы — целые числа в копейках. Скидка округляется до ближайшей копейки,
  сумма к оплате считается как цена минус скидка.
- Остаток от деления суммы на срок рассрочки раздаётся по копейке первым платежам.
- `Idempotency-Key` хранится в уникальной колонке: от дубля при одновременных
  запросах защищает ограничение базы.
- Срок рассрочки при способе оплаты `card` или `sbp` считается ошибкой (422).
- Несуществующий тариф при создании платежа — 404.

## Структура

```
app/
├── api/           # роутеры и зависимости
├── core/          # настройки
├── db/            # движок и сессия
├── models/        # таблицы SQLAlchemy
├── repositories/  # запросы к базе
├── schemas/       # Pydantic-схемы
├── services/      # бизнес-логика
├── constants.py   # тарифы, промокоды, статусы, переходы
└── main.py
tests/
```
