from datetime import date

from app.models.budget import Budget
from app.services import budget_service


def test_budget_vs_actual_computes_variance_and_over_budget_flag(
    db_session, cost_center, category, make_clean_transaction
):
    db_session.add(
        Budget(cost_center_id=cost_center.id, category_id=category.id, period_month=date(2025, 6, 1), currency="USD", budget_amount=1000)
    )
    db_session.flush()
    make_clean_transaction(
        cost_center_id=cost_center.id,
        category_id=category.id,
        transaction_date=date(2025, 6, 15),
        total_amount_base_currency=1200,
    )

    rows = budget_service.budget_vs_actual(db_session, date(2025, 6, 1), date(2025, 6, 30))

    assert len(rows) == 1
    row = rows[0]
    assert row["budget_amount"] == 1000
    assert row["actual_amount"] == 1200
    assert row["variance"] == 200
    assert row["variance_pct"] == 20.0
    assert row["is_over_budget"] is True


def test_budget_vs_actual_reports_zero_actual_when_no_spend_occurred(db_session, cost_center, category):
    db_session.add(
        Budget(cost_center_id=cost_center.id, category_id=category.id, period_month=date(2025, 6, 1), currency="USD", budget_amount=500)
    )
    db_session.flush()

    rows = budget_service.budget_vs_actual(db_session, date(2025, 6, 1), date(2025, 6, 30))

    assert len(rows) == 1
    assert rows[0]["actual_amount"] == 0.0
    assert rows[0]["is_over_budget"] is False


def test_budget_vs_actual_includes_unbudgeted_spend(db_session, cost_center, category, make_clean_transaction):
    # No Budget row exists for this cost center/category/period at all.
    make_clean_transaction(
        cost_center_id=cost_center.id,
        category_id=category.id,
        transaction_date=date(2025, 6, 10),
        total_amount_base_currency=300,
    )

    rows = budget_service.budget_vs_actual(db_session, date(2025, 6, 1), date(2025, 6, 30))

    assert len(rows) == 1
    assert rows[0]["budget_amount"] == 0.0
    assert rows[0]["actual_amount"] == 300
    assert rows[0]["is_over_budget"] is True


def test_burn_down_accumulates_across_months(db_session, cost_center, category, make_clean_transaction):
    db_session.add_all(
        [
            Budget(cost_center_id=cost_center.id, category_id=category.id, period_month=date(2025, 1, 1), currency="USD", budget_amount=100),
            Budget(cost_center_id=cost_center.id, category_id=category.id, period_month=date(2025, 2, 1), currency="USD", budget_amount=100),
        ]
    )
    db_session.flush()
    make_clean_transaction(
        cost_center_id=cost_center.id, category_id=category.id, transaction_date=date(2025, 1, 15), total_amount_base_currency=80
    )
    make_clean_transaction(
        cost_center_id=cost_center.id, category_id=category.id, transaction_date=date(2025, 2, 15), total_amount_base_currency=90
    )

    points = budget_service.burn_down(db_session, 2025)

    assert [p["period_month"] for p in points] == [date(2025, 1, 1), date(2025, 2, 1)]
    assert points[0]["cumulative_budget"] == 100
    assert points[0]["cumulative_actual"] == 80
    assert points[1]["cumulative_budget"] == 200
    assert points[1]["cumulative_actual"] == 170
