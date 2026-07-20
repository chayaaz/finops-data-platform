from datetime import date

from app.models.vendor import Vendor
from app.services import vendor_risk_service


def test_risk_level_thresholds():
    assert vendor_risk_service.risk_level(1000) == "low"
    assert vendor_risk_service.risk_level(1500) == "moderate"
    assert vendor_risk_service.risk_level(2000) == "moderate"
    assert vendor_risk_service.risk_level(2500) == "high"
    assert vendor_risk_service.risk_level(9000) == "high"


def test_vendor_concentration_single_vendor_is_maximally_concentrated(
    db_session, vendor, make_clean_transaction
):
    make_clean_transaction(vendor_id=vendor.id, total_amount_base_currency=1000)

    result = vendor_risk_service.vendor_concentration(db_session, date(2025, 1, 1), date(2025, 12, 31))

    assert result["hhi"] == 10000.0
    assert result["risk_level"] == "high"
    assert len(result["vendor_shares"]) == 1
    assert result["vendor_shares"][0]["share_pct"] == 100.0


def test_vendor_concentration_evenly_split_across_vendors_is_low_risk(
    db_session, category, make_clean_transaction
):
    vendor_a = Vendor(name="Vendor A", default_category_id=category.id)
    vendor_b = Vendor(name="Vendor B", default_category_id=category.id)
    vendor_c = Vendor(name="Vendor C", default_category_id=category.id)
    vendor_d = Vendor(name="Vendor D", default_category_id=category.id)
    db_session.add_all([vendor_a, vendor_b, vendor_c, vendor_d])
    db_session.flush()

    for v in (vendor_a, vendor_b, vendor_c, vendor_d):
        make_clean_transaction(vendor_id=v.id, total_amount_base_currency=250)

    result = vendor_risk_service.vendor_concentration(db_session, date(2025, 1, 1), date(2025, 12, 31))

    # Four equal 25% shares -> HHI = 4 * 25^2 = 2500
    assert result["hhi"] == 2500.0
    assert result["risk_level"] == "high"
    assert len(result["vendor_shares"]) == 4


def test_vendor_concentration_ignores_transactions_outside_period(
    db_session, vendor, make_clean_transaction
):
    make_clean_transaction(vendor_id=vendor.id, total_amount_base_currency=500, transaction_date=date(2024, 1, 1))

    result = vendor_risk_service.vendor_concentration(db_session, date(2025, 1, 1), date(2025, 12, 31))

    assert result["hhi"] == 0.0
    assert result["vendor_shares"] == []
