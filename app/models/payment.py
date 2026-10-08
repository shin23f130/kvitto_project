from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, String, JSON, DateTime, func
from datetime import datetime
from .base import Base



class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    tariff_id: Mapped[int] = mapped_column(ForeignKey("tariffs.id", ondelete="RESTRICT"))
    email: Mapped[str] = mapped_column(String(320))
    method: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20))
    amount: Mapped[int] = mapped_column()
    discount: Mapped[int]  
    installment_months: Mapped[int | None] = mapped_column()
    schedule: Mapped[list[int] | None] = mapped_column(JSON)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )