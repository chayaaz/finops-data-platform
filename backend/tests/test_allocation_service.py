from datetime import date

from app.models.org import Department
from app.services import allocation_service


def test_chargeback_report_splits_shared_cost_by_department_footprint(
    db_session, business_entity, category, make_clean_transaction
):
    shared_category = category
    other_category = category.__class__(name="Office Supplies")
    db_session.add(other_category)
    db_session.flush()

    dept_a = Department(name="Sales", business_entity_id=business_entity.id)
    dept_b = Department(name="R&D", business_entity_id=business_entity.id)
    db_session.add_all([dept_a, dept_b])
    db_session.flush()

    # Shared, centrally-billed cost to be allocated -- not tied to any single department's footprint.
    make_clean_transaction(category_id=shared_category.id, total_amount_base_currency=900, transaction_date=date(2025, 6, 1))

    # Departments' own (non-shared-category) spend defines their relative footprint: 3:1 ratio.
    make_clean_transaction(
        department_id=dept_a.id, category_id=other_category.id, total_amount_base_currency=300, transaction_date=date(2025, 6, 5)
    )
    make_clean_transaction(
        department_id=dept_b.id, category_id=other_category.id, total_amount_base_currency=100, transaction_date=date(2025, 6, 5)
    )

    rows = allocation_service.chargeback_report(db_session, shared_category.id, date(2025, 6, 1), date(2025, 6, 30))

    assert len(rows) == 2
    by_dept = {r["department_name"]: r for r in rows}
    assert by_dept["Sales"]["weight_pct"] == 75.0
    assert by_dept["Sales"]["allocated_amount"] == 675.0
    assert by_dept["R&D"]["weight_pct"] == 25.0
    assert by_dept["R&D"]["allocated_amount"] == 225.0


def test_chargeback_report_returns_empty_when_no_shared_spend_exists(db_session, category):
    rows = allocation_service.chargeback_report(db_session, category.id, date(2025, 6, 1), date(2025, 6, 30))
    assert rows == []


def test_chargeback_report_returns_empty_when_no_department_footprint_exists(
    db_session, category, make_clean_transaction
):
    make_clean_transaction(category_id=category.id, total_amount_base_currency=500, transaction_date=date(2025, 6, 1))

    rows = allocation_service.chargeback_report(db_session, category.id, date(2025, 6, 1), date(2025, 6, 30))
    assert rows == []
