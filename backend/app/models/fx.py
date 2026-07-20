from datetime import date

from sqlalchemy import Date, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ExchangeRate(Base):
    __tablename__ = "exchange_rates"
    __table_args__ = (UniqueConstraint("rate_date", "currency_code", name="uq_exchange_rate_date_currency"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    rate_date: Mapped[date] = mapped_column(Date, index=True)
    currency_code: Mapped[str] = mapped_column(String(3), index=True)
    rate_to_base: Mapped[float] = mapped_column(Numeric(18, 8))
