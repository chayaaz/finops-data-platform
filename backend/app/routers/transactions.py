from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user
from app.models.ingestion import CleanTransaction, RawTransaction
from app.schemas.transaction import CleanTransactionRead, RawTransactionRead, TransactionPage

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=TransactionPage)
def list_transactions(
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
    date_from: date | None = None,
    date_to: date | None = None,
    vendor_id: int | None = None,
    department_id: int | None = None,
    cost_center_id: int | None = None,
    category_id: int | None = None,
    business_entity_id: int | None = None,
    region_id: int | None = None,
    currency: str | None = None,
    skip: int = 0,
    limit: int = Query(default=50, le=500),
) -> TransactionPage:
    query = db.query(CleanTransaction)

    if date_from is not None:
        query = query.filter(CleanTransaction.transaction_date >= date_from)
    if date_to is not None:
        query = query.filter(CleanTransaction.transaction_date <= date_to)
    if vendor_id is not None:
        query = query.filter(CleanTransaction.vendor_id == vendor_id)
    if department_id is not None:
        query = query.filter(CleanTransaction.department_id == department_id)
    if cost_center_id is not None:
        query = query.filter(CleanTransaction.cost_center_id == cost_center_id)
    if category_id is not None:
        query = query.filter(CleanTransaction.category_id == category_id)
    if business_entity_id is not None:
        query = query.filter(CleanTransaction.business_entity_id == business_entity_id)
    if region_id is not None:
        query = query.filter(CleanTransaction.region_id == region_id)
    if currency is not None:
        query = query.filter(CleanTransaction.currency == currency)

    total = query.count()
    items = (
        query.order_by(CleanTransaction.transaction_date.desc()).offset(skip).limit(limit).all()
    )

    return TransactionPage(items=items, total=total, skip=skip, limit=limit)


@router.get("/raw", response_model=list[RawTransactionRead])
def list_raw_transactions(
    batch_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
    skip: int = 0,
    limit: int = Query(default=100, le=1000),
) -> list[RawTransactionRead]:
    return (
        db.query(RawTransaction)
        .filter(RawTransaction.batch_id == batch_id)
        .order_by(RawTransaction.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
