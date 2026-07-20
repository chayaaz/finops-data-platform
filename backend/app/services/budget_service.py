from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.budget import Budget
from app.models.ingestion import CleanTransaction


def budget_vs_actual(
    db: Session,
    period_start: date,
    period_end: date,
    cost_center_id: int | None = None,
    category_id: int | None = None,
) -> list[dict]:
    budget_query = db.query(
        Budget.cost_center_id,
        Budget.category_id,
        Budget.period_month,
        func.sum(Budget.budget_amount).label("budget_amount"),
    ).filter(Budget.period_month.between(period_start, period_end))

    if cost_center_id is not None:
        budget_query = budget_query.filter(Budget.cost_center_id == cost_center_id)
    if category_id is not None:
        budget_query = budget_query.filter(Budget.category_id == category_id)

    budget_query = budget_query.group_by(Budget.cost_center_id, Budget.category_id, Budget.period_month)

    actual_query = (
        db.query(
            CleanTransaction.cost_center_id,
            CleanTransaction.category_id,
            func.date_trunc("month", CleanTransaction.transaction_date).label("period_month"),
            func.sum(CleanTransaction.total_amount_base_currency).label("actual_amount"),
        )
        .filter(CleanTransaction.transaction_date.between(period_start, period_end))
        .filter(CleanTransaction.total_amount_base_currency.isnot(None))
    )
    if cost_center_id is not None:
        actual_query = actual_query.filter(CleanTransaction.cost_center_id == cost_center_id)
    if category_id is not None:
        actual_query = actual_query.filter(CleanTransaction.category_id == category_id)

    actual_query = actual_query.group_by(
        CleanTransaction.cost_center_id, CleanTransaction.category_id, "period_month"
    )

    actuals = {
        (cc_id, cat_id, period.date()): float(amount)
        for cc_id, cat_id, period, amount in actual_query.all()
    }

    results = []
    seen_keys = set()
    for cc_id, cat_id, period_month, budget_amount in budget_query.all():
        key = (cc_id, cat_id, period_month)
        seen_keys.add(key)
        actual_amount = actuals.get(key, 0.0)
        results.append(_variance_row(cc_id, cat_id, period_month, float(budget_amount), actual_amount))

    for (cc_id, cat_id, period_month), actual_amount in actuals.items():
        if (cc_id, cat_id, period_month) not in seen_keys:
            results.append(_variance_row(cc_id, cat_id, period_month, 0.0, actual_amount))

    return sorted(results, key=lambda r: (r["period_month"], r["cost_center_id"] or 0))


def _variance_row(cc_id: int | None, cat_id: int | None, period_month: date, budget_amount: float, actual_amount: float) -> dict:
    variance = actual_amount - budget_amount
    variance_pct = (variance / budget_amount * 100) if budget_amount else None
    return {
        "cost_center_id": cc_id,
        "category_id": cat_id,
        "period_month": period_month,
        "budget_amount": round(budget_amount, 2),
        "actual_amount": round(actual_amount, 2),
        "variance": round(variance, 2),
        "variance_pct": round(variance_pct, 1) if variance_pct is not None else None,
        "is_over_budget": variance > 0,
    }


def burn_down(db: Session, year: int, cost_center_id: int | None = None, category_id: int | None = None) -> list[dict]:
    rows = budget_vs_actual(db, date(year, 1, 1), date(year, 12, 31), cost_center_id, category_id)

    by_month: dict[date, dict] = {}
    for row in rows:
        month_key = row["period_month"].replace(day=1)
        bucket = by_month.setdefault(month_key, {"budget_amount": 0.0, "actual_amount": 0.0})
        bucket["budget_amount"] += row["budget_amount"]
        bucket["actual_amount"] += row["actual_amount"]

    cumulative_budget = 0.0
    cumulative_actual = 0.0
    result = []
    for month_key in sorted(by_month):
        cumulative_budget += by_month[month_key]["budget_amount"]
        cumulative_actual += by_month[month_key]["actual_amount"]
        result.append(
            {
                "period_month": month_key,
                "cumulative_budget": round(cumulative_budget, 2),
                "cumulative_actual": round(cumulative_actual, 2),
            }
        )
    return result
