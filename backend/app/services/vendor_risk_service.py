from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.ingestion import CleanTransaction
from app.models.vendor import Vendor


def risk_level(hhi: float) -> str:
    if hhi < 1500:
        return "low"
    if hhi < 2500:
        return "moderate"
    return "high"


def vendor_concentration(
    db: Session,
    period_start: date,
    period_end: date,
    business_entity_id: int | None = None,
    category_id: int | None = None,
) -> dict:
    """Herfindahl-Hirschman Index of vendor spend concentration: sum of each vendor's
    squared market share (x10,000). A standard procurement-risk metric that requires
    aggregating and re-weighting the full transaction set, not a single pivot."""
    query = (
        db.query(Vendor.id, Vendor.name, func.sum(CleanTransaction.total_amount_base_currency).label("total"))
        .join(CleanTransaction, CleanTransaction.vendor_id == Vendor.id)
        .filter(CleanTransaction.transaction_date.between(period_start, period_end))
        .filter(CleanTransaction.total_amount_base_currency.isnot(None))
    )
    if business_entity_id is not None:
        query = query.filter(CleanTransaction.business_entity_id == business_entity_id)
    if category_id is not None:
        query = query.filter(CleanTransaction.category_id == category_id)

    rows = query.group_by(Vendor.id, Vendor.name).all()
    grand_total = sum(float(total) for _, _, total in rows)

    if grand_total <= 0:
        return {"hhi": 0.0, "risk_level": "low", "vendor_shares": []}

    vendor_shares = []
    hhi = 0.0
    for vendor_id, vendor_name, total in rows:
        share_pct = float(total) / grand_total * 100
        hhi += share_pct**2
        vendor_shares.append({"vendor_id": vendor_id, "vendor_name": vendor_name, "spend": round(float(total), 2), "share_pct": round(share_pct, 2)})

    vendor_shares.sort(key=lambda v: v["spend"], reverse=True)

    return {
        "hhi": round(hhi, 1),
        "risk_level": risk_level(hhi),
        "total_spend": round(grand_total, 2),
        "vendor_shares": vendor_shares,
    }
