from app.models.ingestion import CleanTransaction, IngestionBatch, RawTransaction
from app.models.quality import DataQualityIssue
from app.services import cleaning_service


def _add_raw(db_session, batch, **overrides) -> RawTransaction:
    defaults = dict(
        batch_id=batch.id,
        record_id="TX-0001",
        vendor_name="Amazon Web Services",
        department="Engineering",
        cost_center="CC-100",
        category="Cloud Infrastructure",
        business_entity="FinOps HQ",
        transaction_date="2025-06-15",
        currency="USD",
        net_amount="100.00",
        tax_amount="0.00",
        total_amount="100.00",
        payment_method="credit card",
        approval_status="approved",
    )
    defaults.update(overrides)
    raw = RawTransaction(**defaults)
    db_session.add(raw)
    db_session.flush()
    return raw


def test_process_batch_accepts_a_clean_row(db_session, batch, vendor, department, cost_center, category, cleaning_rules):
    _add_raw(db_session, batch)

    cleaning_service.process_batch(db_session, batch)

    assert batch.accepted_count == 1
    assert batch.rejected_count == 0
    clean = db_session.query(CleanTransaction).one()
    assert clean.vendor_id == vendor.id
    assert clean.department_id == department.id
    assert clean.cost_center_id == cost_center.id
    assert clean.category_id == category.id
    assert db_session.query(DataQualityIssue).count() == 0


def test_process_batch_rejects_duplicate_record_id_against_existing_clean_transactions(
    db_session, batch, admin_user, vendor, cleaning_rules, make_clean_transaction
):
    earlier_batch = IngestionBatch(file_name="earlier_batch.csv", uploaded_by_id=admin_user.id)
    db_session.add(earlier_batch)
    db_session.flush()
    make_clean_transaction(vendor_id=vendor.id, batch_id=earlier_batch.id)
    existing_record_id = db_session.query(CleanTransaction).one().record_id
    _add_raw(db_session, batch, record_id=existing_record_id)

    cleaning_service.process_batch(db_session, batch)

    assert batch.rejected_count == 1
    assert batch.accepted_count == 0
    issue = db_session.query(DataQualityIssue).filter(DataQualityIssue.rule_code == "DUPLICATE_RECORD_ID").one()
    assert existing_record_id in issue.description


def test_process_batch_rejects_duplicate_record_id_within_same_batch(db_session, batch, vendor, cleaning_rules):
    _add_raw(db_session, batch, record_id="TX-DUP")
    _add_raw(db_session, batch, record_id="TX-DUP")

    cleaning_service.process_batch(db_session, batch)

    assert batch.accepted_count == 1
    assert batch.rejected_count == 1


def test_process_batch_rejects_unparseable_transaction_date(db_session, batch, vendor, cleaning_rules):
    _add_raw(db_session, batch, transaction_date="not-a-date")

    cleaning_service.process_batch(db_session, batch)

    assert batch.rejected_count == 1
    assert batch.accepted_count == 0
    issue = db_session.query(DataQualityIssue).one()
    assert issue.rule_code == "MISSING_DATE"


def test_process_batch_flags_missing_vendor_but_still_accepts_row(db_session, batch, cleaning_rules):
    _add_raw(db_session, batch, vendor_name="")

    cleaning_service.process_batch(db_session, batch)

    assert batch.accepted_count == 1
    clean = db_session.query(CleanTransaction).one()
    assert clean.vendor_id is None
    issue = db_session.query(DataQualityIssue).filter(DataQualityIssue.rule_code == "MISSING_VENDOR").one()
    assert issue.clean_transaction_id == clean.id


def test_process_batch_flags_unknown_vendor_not_in_master_data(db_session, batch, cleaning_rules):
    _add_raw(db_session, batch, vendor_name="Totally Unknown Vendor Inc")

    cleaning_service.process_batch(db_session, batch)

    assert batch.accepted_count == 1
    clean = db_session.query(CleanTransaction).one()
    assert clean.vendor_id is None
    assert db_session.query(DataQualityIssue).filter(DataQualityIssue.rule_code == "UNKNOWN_VENDOR").count() == 1


def test_process_batch_flags_negative_amount_but_still_accepts_row(db_session, batch, vendor, cleaning_rules):
    _add_raw(db_session, batch, total_amount="-50.00", net_amount="-50.00")

    cleaning_service.process_batch(db_session, batch)

    assert batch.accepted_count == 1
    clean = db_session.query(CleanTransaction).one()
    assert float(clean.total_amount) == -50.00
    assert db_session.query(DataQualityIssue).filter(DataQualityIssue.rule_code == "NEGATIVE_AMOUNT").count() == 1


def test_process_batch_flags_total_less_than_net_as_invalid_amount(db_session, batch, vendor, cleaning_rules):
    _add_raw(db_session, batch, net_amount="200.00", total_amount="100.00")

    cleaning_service.process_batch(db_session, batch)

    assert batch.accepted_count == 1
    assert db_session.query(DataQualityIssue).filter(DataQualityIssue.rule_code == "INVALID_AMOUNT").count() == 1


def test_process_batch_normalizes_currency_aliases_and_payment_method(db_session, batch, vendor, cleaning_rules):
    _add_raw(db_session, batch, currency="US Dollar", payment_method="wire")

    cleaning_service.process_batch(db_session, batch)

    clean = db_session.query(CleanTransaction).one()
    assert clean.currency == "USD"
    assert clean.payment_method == "Wire Transfer"


def test_process_batch_updates_batch_row_counts(db_session, batch, vendor, cleaning_rules):
    _add_raw(db_session, batch, record_id="TX-A")
    _add_raw(db_session, batch, record_id="TX-B", vendor_name="")
    _add_raw(db_session, batch, record_id="TX-C", transaction_date="garbage")

    cleaning_service.process_batch(db_session, batch)

    assert batch.row_count == 3
    assert batch.accepted_count == 2
    assert batch.rejected_count == 1
