from datetime import date

from app.services.normalization import (
    normalize_currency,
    normalize_payment_method,
    parse_amount,
    parse_date,
)


def test_normalize_currency_recognizes_aliases():
    assert normalize_currency("US Dollar") == "USD"
    assert normalize_currency("nis") == "ILS"
    assert normalize_currency("£") == "GBP"


def test_normalize_currency_accepts_bare_iso_code():
    assert normalize_currency("cad") == "CAD"


def test_normalize_currency_rejects_garbage():
    assert normalize_currency("not a currency") is None
    assert normalize_currency(None) is None
    assert normalize_currency("  ") is None


def test_normalize_payment_method_aliases():
    assert normalize_payment_method("wire") == "Wire Transfer"
    assert normalize_payment_method("CC") == "Credit Card"


def test_normalize_payment_method_falls_back_to_title_case():
    assert normalize_payment_method("paypal") == "Paypal"


def test_parse_date_accepts_multiple_formats():
    assert parse_date("2025-03-14") == date(2025, 3, 14)
    assert parse_date("14/03/2025") == date(2025, 3, 14)


def test_parse_date_rejects_unparseable_text():
    assert parse_date("not a date") is None
    assert parse_date(None) is None


def test_parse_amount_strips_thousands_separators():
    assert parse_amount("1,234.50") == 1234.50


def test_parse_amount_rejects_non_numeric():
    assert parse_amount("free") is None
    assert parse_amount(None) is None
