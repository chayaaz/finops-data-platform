from datetime import date

from app.services import anomaly_service


def test_leading_digit_extracts_first_significant_digit():
    assert anomaly_service.leading_digit(123.45) == 1
    assert anomaly_service.leading_digit(987.0) == 9
    assert anomaly_service.leading_digit(0.0456) == 4


def test_leading_digit_of_zero_is_none():
    assert anomaly_service.leading_digit(0.0) is None


def test_detect_zscore_anomalies_flags_only_the_outlier(db_session, vendor, make_clean_transaction):
    for _ in range(20):
        make_clean_transaction(vendor_id=vendor.id, total_amount_base_currency=100.0)
    outlier = make_clean_transaction(vendor_id=vendor.id, total_amount_base_currency=5_000.0)

    created = anomaly_service.detect_zscore_anomalies(db_session)

    assert created == 1
    anomalies = db_session.query(anomaly_service.Anomaly).all()
    assert len(anomalies) == 1
    assert anomalies[0].clean_transaction_id == outlier.id
    assert anomalies[0].anomaly_type == "AMOUNT_ZSCORE"


def test_detect_zscore_anomalies_skips_vendors_below_minimum_sample_size(
    db_session, vendor, make_clean_transaction
):
    make_clean_transaction(vendor_id=vendor.id, total_amount_base_currency=100.0)
    make_clean_transaction(vendor_id=vendor.id, total_amount_base_currency=999_999.0)

    created = anomaly_service.detect_zscore_anomalies(db_session)

    assert created == 0


def test_detect_zscore_anomalies_is_idempotent(db_session, vendor, make_clean_transaction):
    for _ in range(20):
        make_clean_transaction(vendor_id=vendor.id, total_amount_base_currency=100.0)
    make_clean_transaction(vendor_id=vendor.id, total_amount_base_currency=5_000.0)

    first_run = anomaly_service.detect_zscore_anomalies(db_session)
    second_run = anomaly_service.detect_zscore_anomalies(db_session)

    assert first_run == 1
    assert second_run == 0


def test_benford_distribution_flags_a_heavily_skewed_group(db_session, category, make_clean_transaction):
    # 30 transactions all starting with digit 1 -- wildly inconsistent with Benford's Law,
    # which expects ~30% (not 100%) of leading digits to be 1.
    for _ in range(30):
        make_clean_transaction(category_id=category.id, total_amount_base_currency=111.0)

    results = anomaly_service.benford_distribution(db_session, group_by="category")

    assert len(results) == 1
    group = results[0]
    assert group["group_id"] == category.id
    assert group["sample_size"] == 30
    assert group["observed_distribution"][1] == 1.0
    assert bool(group["flagged"]) is True


def test_benford_distribution_excludes_groups_below_sample_threshold(
    db_session, category, make_clean_transaction
):
    for _ in range(10):
        make_clean_transaction(category_id=category.id, total_amount_base_currency=111.0)

    results = anomaly_service.benford_distribution(db_session, group_by="category")

    assert results == []
