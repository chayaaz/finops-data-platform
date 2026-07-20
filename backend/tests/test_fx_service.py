from datetime import date

from app.models.fx import ExchangeRate
from app.services import fx_service


def test_base_currency_rate_is_always_one(db_session):
    assert fx_service.get_rate_to_base(db_session, "USD", date(2025, 6, 1)) == 1.0


def test_get_rate_to_base_uses_latest_rate_on_or_before_transaction_date(db_session):
    db_session.add_all(
        [
            ExchangeRate(rate_date=date(2025, 1, 1), currency_code="EUR", rate_to_base=1.05),
            ExchangeRate(rate_date=date(2025, 6, 1), currency_code="EUR", rate_to_base=1.10),
            ExchangeRate(rate_date=date(2025, 9, 1), currency_code="EUR", rate_to_base=1.15),
        ]
    )
    db_session.flush()

    # A transaction on 2025-07-15 should use the 2025-06-01 rate, not an earlier or later one.
    rate = fx_service.get_rate_to_base(db_session, "EUR", date(2025, 7, 15))
    assert rate == 1.10


def test_get_rate_to_base_returns_none_when_no_rate_exists_yet(db_session):
    db_session.add(ExchangeRate(rate_date=date(2025, 6, 1), currency_code="EUR", rate_to_base=1.10))
    db_session.flush()

    rate = fx_service.get_rate_to_base(db_session, "EUR", date(2025, 1, 1))
    assert rate is None


def test_convert_to_base_applies_point_in_time_rate(db_session):
    db_session.add(ExchangeRate(rate_date=date(2025, 1, 1), currency_code="GBP", rate_to_base=1.25))
    db_session.flush()

    converted = fx_service.convert_to_base(db_session, 100, "GBP", date(2025, 3, 1))
    assert converted == 125.0


def test_convert_to_base_propagates_missing_rate_as_none(db_session):
    converted = fx_service.convert_to_base(db_session, 100, "JPY", date(2025, 3, 1))
    assert converted is None
