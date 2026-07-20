from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user, require_roles
from app.models.enums import AnomalyStatus, UserRole
from app.models.quality import Anomaly
from app.models.user import User
from app.schemas.anomaly import AnomalyRead, AnomalyStatusUpdate, BenfordGroupResult
from app.services import anomaly_service
from app.services.audit_service import log_action

router = APIRouter(prefix="/anomalies", tags=["anomalies"])


@router.get("", response_model=list[AnomalyRead])
def list_anomalies(
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
    status_filter: AnomalyStatus | None = Query(default=None, alias="status"),
    skip: int = 0,
    limit: int = Query(default=100, le=1000),
) -> list[AnomalyRead]:
    query = db.query(Anomaly)
    if status_filter is not None:
        query = query.filter(Anomaly.status == status_filter)
    return query.order_by(Anomaly.detected_at.desc()).offset(skip).limit(limit).all()


@router.get("/benford", response_model=list[BenfordGroupResult])
def benford(
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
    group_by: str = Query(default="category", pattern="^(category|vendor)$"),
) -> list[BenfordGroupResult]:
    return anomaly_service.benford_distribution(db, group_by=group_by)


@router.post("/detect")
def trigger_detection(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.FINANCE_MANAGER)),
) -> dict[str, int]:
    created = anomaly_service.detect_zscore_anomalies(db)
    log_action(db, user.id, "anomaly_detection_run", "anomaly", details=f"created={created}")
    db.commit()
    return {"created": created}


@router.patch("/{anomaly_id}", response_model=AnomalyRead)
def update_anomaly_status(
    anomaly_id: int,
    payload: AnomalyStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.FINANCE_MANAGER, UserRole.ANALYST)),
) -> AnomalyRead:
    anomaly = db.get(Anomaly, anomaly_id)
    if anomaly is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anomaly not found")

    anomaly.status = payload.status
    if payload.status in (AnomalyStatus.REVIEWED, AnomalyStatus.DISMISSED):
        anomaly.reviewed_by_id = user.id
        anomaly.reviewed_at = datetime.now(timezone.utc)

    log_action(db, user.id, f"anomaly_status_changed_to_{payload.status.value}", "anomaly", str(anomaly_id))
    db.commit()
    db.refresh(anomaly)
    return anomaly
