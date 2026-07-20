from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.ingestion import CleanTransaction
from app.models.org import Department


def chargeback_report(
    db: Session, shared_category_id: int, period_start: date, period_end: date
) -> list[dict]:
    """Splits a centrally-billed shared cost (e.g. company-wide 'Cloud Infrastructure')
    across departments, weighted by each department's share of all other spend in the
    same period -- a proxy for relative organizational footprint since no headcount
    dimension exists. Re-weights dynamically per period, which a static spreadsheet
    formula would not do without manual upkeep."""
    shared_total = (
        db.query(func.sum(CleanTransaction.total_amount_base_currency))
        .filter(
            CleanTransaction.category_id == shared_category_id,
            CleanTransaction.transaction_date.between(period_start, period_end),
            CleanTransaction.total_amount_base_currency.isnot(None),
        )
        .scalar()
    ) or 0.0
    shared_total = float(shared_total)

    if shared_total <= 0:
        return []

    footprint_rows = (
        db.query(Department.id, Department.name, func.sum(CleanTransaction.total_amount_base_currency).label("footprint"))
        .join(CleanTransaction, CleanTransaction.department_id == Department.id)
        .filter(
            CleanTransaction.category_id != shared_category_id,
            CleanTransaction.transaction_date.between(period_start, period_end),
            CleanTransaction.total_amount_base_currency.isnot(None),
        )
        .group_by(Department.id, Department.name)
        .all()
    )

    total_footprint = sum(float(footprint) for _, _, footprint in footprint_rows)
    if total_footprint <= 0:
        return []

    allocation = []
    for dept_id, dept_name, footprint in footprint_rows:
        weight = float(footprint) / total_footprint
        allocation.append(
            {
                "department_id": dept_id,
                "department_name": dept_name,
                "weight_pct": round(weight * 100, 2),
                "allocated_amount": round(shared_total * weight, 2),
            }
        )

    return sorted(allocation, key=lambda a: a["allocated_amount"], reverse=True)
