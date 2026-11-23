from app.models.enums import IssueStatus, UserRole
from app.models.ingestion import CleanTransaction, IngestionBatch
from app.models.quality import DataQualityIssue
from app.services import cleaning_service
from tests.conftest import auth_headers, make_user
from tests.test_cleaning_service import _add_raw


def _issue(db_session, rule_code: str) -> DataQualityIssue:
    return db_session.query(DataQualityIssue).filter(DataQualityIssue.rule_code == rule_code).one()


def test_fixing_a_rejected_row_adds_it_to_clean_transactions(
    client, db_session, batch, admin_user, vendor, cleaning_rules, cost_center
):
    _add_raw(db_session, batch, transaction_date="not a date")
    cleaning_service.process_batch(db_session, batch)
    assert batch.rejected_count == 1
    issue = _issue(db_session, "MISSING_DATE")

    response = client.post(
        f"/issues/{issue.id}/fix", json={"transaction_date": "2025-06-20"}, headers=auth_headers(admin_user)
    )

    assert response.status_code == 200
    assert response.json()["was_added"] is True
    db_session.expire_all()
    clean = db_session.query(CleanTransaction).one()
    assert clean.transaction_date.isoformat() == "2025-06-20"
    refreshed_batch = db_session.get(IngestionBatch, batch.id)
    assert refreshed_batch.accepted_count == 1
    assert refreshed_batch.rejected_count == 0
    assert db_session.get(DataQualityIssue, issue.id).status == IssueStatus.RESOLVED


def test_fixing_an_accepted_row_updates_its_clean_transaction(
    client, db_session, batch, admin_user, vendor, cleaning_rules, cost_center
):
    _add_raw(db_session, batch, vendor_name="")
    cleaning_service.process_batch(db_session, batch)
    issue = _issue(db_session, "MISSING_VENDOR")

    response = client.post(
        f"/issues/{issue.id}/fix", json={"vendor_name": "Amazon Web Services"}, headers=auth_headers(admin_user)
    )

    assert response.status_code == 200
    body = response.json()
    assert body["was_added"] is False
    assert body["remaining_problems"] == []
    db_session.expire_all()
    assert db_session.query(CleanTransaction).count() == 1
    assert db_session.query(CleanTransaction).one().vendor_id == vendor.id


def test_fix_that_leaves_row_invalid_is_rejected_without_changes(
    client, db_session, batch, admin_user, vendor, cleaning_rules, cost_center
):
    _add_raw(db_session, batch, transaction_date="")
    cleaning_service.process_batch(db_session, batch)
    issue = _issue(db_session, "MISSING_DATE")

    response = client.post(
        f"/issues/{issue.id}/fix", json={"transaction_date": "still bad"}, headers=auth_headers(admin_user)
    )

    assert response.status_code == 400
    db_session.expire_all()
    assert db_session.query(CleanTransaction).count() == 0
    assert db_session.get(DataQualityIssue, issue.id).status == IssueStatus.OPEN


def test_fix_flags_problems_that_remain_after_the_correction(
    client, db_session, batch, admin_user, vendor, cleaning_rules, cost_center
):
    _add_raw(db_session, batch, transaction_date="")
    cleaning_service.process_batch(db_session, batch)
    issue = _issue(db_session, "MISSING_DATE")

    response = client.post(
        f"/issues/{issue.id}/fix",
        json={"transaction_date": "2025-06-20", "vendor_name": "Unknown Supplier"},
        headers=auth_headers(admin_user),
    )

    assert response.status_code == 200
    assert response.json()["remaining_problems"] == ["Vendor 'Unknown Supplier' not in master data"]
    db_session.expire_all()
    assert _issue(db_session, "UNKNOWN_VENDOR").status == IssueStatus.OPEN


def test_auditor_cannot_fix_rows(client, db_session, batch, vendor, cleaning_rules):
    _add_raw(db_session, batch, vendor_name="")
    cleaning_service.process_batch(db_session, batch)
    issue = _issue(db_session, "MISSING_VENDOR")
    auditor = make_user(db_session, "auditor@test.io", UserRole.AUDITOR)

    response = client.post(f"/issues/{issue.id}/fix", json={"vendor_name": "X"}, headers=auth_headers(auditor))

    assert response.status_code == 403


def test_issue_summary_can_be_limited_to_one_batch(
    client, db_session, batch, admin_user, vendor, cost_center, cleaning_rules
):
    other_batch = IngestionBatch(file_name="other.csv", uploaded_by_id=admin_user.id)
    db_session.add(other_batch)
    db_session.flush()
    _add_raw(db_session, batch, vendor_name="")
    _add_raw(db_session, other_batch, record_id="TX-0002", transaction_date="")
    cleaning_service.process_batch(db_session, batch)
    cleaning_service.process_batch(db_session, other_batch)

    response = client.get("/issues/summary", params={"batch_id": batch.id}, headers=auth_headers(admin_user))

    assert response.status_code == 200
    assert response.json()["by_rule_code"] == {"MISSING_VENDOR": 1}
