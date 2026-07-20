from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user
from app.models.budget import Commitment
from app.models.org import BusinessEntity
from app.models.vendor import Vendor
from app.schemas.vendor import CommitmentUtilization, VendorConcentration, VendorRead
from app.services import vendor_risk_service

router = APIRouter(prefix="/vendors", tags=["vendors"])


@router.get("", response_model=list[VendorRead])
def list_vendors(db: Session = Depends(get_db), _user=Depends(get_current_user)) -> list[VendorRead]:
    return db.query(Vendor).order_by(Vendor.name).all()


@router.get("/concentration", response_model=VendorConcentration)
def concentration(
    period_start: date,
    period_end: date,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
    business_entity_id: int | None = None,
    category_id: int | None = None,
) -> VendorConcentration:
    return vendor_risk_service.vendor_concentration(db, period_start, period_end, business_entity_id, category_id)


@router.get("/commitments", response_model=list[CommitmentUtilization])
def commitments(
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
    period_start: date | None = None,
    period_end: date | None = None,
    vendor_id: int | None = None,
) -> list[CommitmentUtilization]:
    query = db.query(Commitment, Vendor.name, BusinessEntity.name).join(Vendor).join(BusinessEntity)
    if period_start is not None:
        query = query.filter(Commitment.period_month >= period_start)
    if period_end is not None:
        query = query.filter(Commitment.period_month <= period_end)
    if vendor_id is not None:
        query = query.filter(Commitment.vendor_id == vendor_id)

    results = []
    for commitment, vendor_name, entity_name in query.order_by(Commitment.period_month.desc()).all():
        committed = float(commitment.committed_amount)
        utilized = float(commitment.utilized_amount)
        results.append(
            CommitmentUtilization(
                vendor_id=commitment.vendor_id,
                vendor_name=vendor_name,
                business_entity_id=commitment.business_entity_id,
                business_entity_name=entity_name,
                period_month=commitment.period_month,
                currency=commitment.currency,
                committed_amount=committed,
                utilized_amount=utilized,
                utilization_pct=round(utilized / committed * 100, 1) if committed else 0.0,
            )
        )
    return results
