from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Tariff
from app.constants import DEFAULT_TARIFFS
from app.api.routers import tariff, payment, webhook


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with SessionLocal() as session:
        if await session.scalar(select(Tariff.id).limit(1)) is None:
            session.add_all(Tariff(**item) for item in DEFAULT_TARIFFS)
            await session.commit()
    yield
    
    
    
app = FastAPI(title="Kvitto payments", lifespan=lifespan)

app.include_router(tariff.router)
app.include_router(payment.router)
app.include_router(webhook.router)