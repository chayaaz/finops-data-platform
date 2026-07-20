from datetime import date

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.fx import ExchangeRate

settings = get_settings()


def get_rate_to_base(db: Session, currency_code: str, on_date: date) -> float | None:
    if currency_code == settings.base_currency:
        return 1.0

    rate_row = (
        db.query(ExchangeRate)
        .filter(ExchangeRate.currency_code == currency_code, ExchangeRate.rate_date <= on_date)
        .order_by(ExchangeRate.rate_date.desc())
        .first()
    )
    return float(rate_row.rate_to_base) if rate_row else None


def convert_to_base(db: Session, amount: float, currency_code: str, on_date: date) -> float | None:
    rate = get_rate_to_base(db, currency_code, on_date)
    if rate is None:
        return None
    return round(amount * rate, 2)
