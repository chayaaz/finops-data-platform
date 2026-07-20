from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user
from app.models.ingestion import CleanTransaction
from app.models.quality import Anomaly, DataQualityIssue
from app.models.vendor import Category
from app.schemas.analytics import AllocationRow, DashboardKpis, ForecastResult, FxExposureRow, TrendPoint
from app.services import allocation_service, forecasting_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _month_start(d: date) -> date:
    return d.replace(day=1)


def _prev_month(d: date) -> date:
    if d.month == 1:
        return date(d.year - 1, 12, 1)
    return date(d.year, d.month - 1, 1)


@router.get("/kpis", response_model=DashboardKpis)
def kpis(db: Session = Depends(get_db), _user=Depends(get_current_user)) -> DashboardKpis:
    total_spend = db.query(func.sum(CleanTransaction.total_amount_base_currency)).scalar() or 0.0
    total_transactions = db.query(func.count(CleanTransaction.id)).scalar() or 0

    open_issues = db.query(func.count(DataQualityIssue.id)).filter(DataQualityIssue.status == "open").scalar() or 0
    open_anomalies = db.query(func.count(Anomaly.id)).filter(Anomaly.status == "open").scalar() or 0

    flagged_transactions = db.query(func.count(func.distinct(DataQualityIssue.clean_transaction_id))).scalar() or 0
    clean_no_issue = total_transactions - flagged_transactions
    quality_score = round(clean_no_issue / total_transactions * 100, 1) if total_transactions else 100.0

    latest_month = db.query(func.max(func.date_trunc("month", CleanTransaction.transaction_date))).scalar()
    mom_growth = None
    if latest_month:
        current_total = (
            db.query(func.sum(CleanTransaction.total_amount_base_currency))
            .filter(func.date_trunc("month", CleanTransaction.transaction_date) == latest_month)
            .scalar()
            or 0.0
        )
        prev_month = _prev_month(latest_month.date())
        prev_total = (
            db.query(func.sum(CleanTransaction.total_amount_base_currency))
            .filter(func.date_trunc("month", CleanTransaction.transaction_date) == prev_month)
            .scalar()
            or 0.0
        )
        if prev_total:
            mom_growth = round((float(current_total) - float(prev_total)) / float(prev_total) * 100, 1)

    top_category = (
        db.query(Category.name, func.sum(CleanTransaction.total_amount_base_currency).label("total"))
        .join(CleanTransaction, CleanTransaction.category_id == Category.id)
        .group_by(Category.name)
        .order_by(func.sum(CleanTransaction.total_amount_base_currency).desc())
        .first()
    )

    return DashboardKpis(
        total_spend=round(float(total_spend), 2),
        total_transactions=total_transactions,
        open_issues=open_issues,
        open_anomalies=open_anomalies,
        data_quality_score_pct=quality_score,
        mom_growth_pct=mom_growth,
        top_category_name=top_category[0] if top_category else None,
        top_category_spend=round(float(top_category[1]), 2) if top_category else None,
    )


@router.get("/trends", response_model=list[TrendPoint])
def trends(
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
    category_id: int | None = None,
) -> list[TrendPoint]:
    query = db.query(
        func.date_trunc("month", CleanTransaction.transaction_date).label("period_month"),
        func.sum(CleanTransaction.total_amount_base_currency).label("total"),
    ).filter(CleanTransaction.total_amount_base_currency.isnot(None))

    if category_id is not None:
        query = query.filter(CleanTransaction.category_id == category_id)

    rows = query.group_by("period_month").order_by("period_month").all()
    return [TrendPoint(period_month=period.date(), total_spend=round(float(total), 2)) for period, total in rows]


@router.get("/forecast", response_model=ForecastResult)
def forecast(
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
    category_id: int | None = None,
    months_ahead: int = 3,
) -> ForecastResult:
    return forecasting_service.forecast_category_spend(db, category_id, months_ahead)


@router.get("/allocation", response_model=list[AllocationRow])
def allocation(
    category_id: int,
    period_start: date,
    period_end: date,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
) -> list[AllocationRow]:
    return allocation_service.chargeback_report(db, category_id, period_start, period_end)


@router.get("/fx-exposure", response_model=list[FxExposureRow])
def fx_exposure(db: Session = Depends(get_db), _user=Depends(get_current_user)) -> list[FxExposureRow]:
    rows = (
        db.query(
            CleanTransaction.currency,
            func.sum(CleanTransaction.total_amount_base_currency).label("total"),
            func.count(CleanTransaction.id).label("count"),
        )
        .filter(CleanTransaction.total_amount_base_currency.isnot(None))
        .group_by(CleanTransaction.currency)
        .all()
    )
    grand_total = sum(float(total) for _, total, _ in rows) or 1.0
    return [
        FxExposureRow(
            currency=currency,
            total_base_currency=round(float(total), 2),
            share_pct=round(float(total) / grand_total * 100, 1),
            transaction_count=count,
        )
        for currency, total, count in sorted(rows, key=lambda r: r[1], reverse=True)
    ]
