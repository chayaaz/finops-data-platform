from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user, require_roles
from app.models.enums import IssueStatus, UserRole
from app.models.quality import DataQualityIssue
from app.models.user import User
from app.schemas.issue import DataQualityIssueRead, IssueStatusUpdate, IssueSummary
from app.services.audit_service import log_action

router = APIRouter(prefix="/issues", tags=["issues"])


@router.get("", response_model=list[DataQualityIssueRead])
def list_issues(
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
    status_filter: IssueStatus | None = Query(default=None, alias="status"),
    severity: str | None = None,
    batch_id: int | None = None,
    skip: int = 0,
    limit: int = Query(default=100, le=1000),
) -> list[DataQualityIssueRead]:
    query = db.query(DataQualityIssue)
    if status_filter is not None:
        query = query.filter(DataQualityIssue.status == status_filter)
    if severity is not None:
        query = query.filter(DataQualityIssue.severity == severity)
    if batch_id is not None:
        query = query.filter(DataQualityIssue.batch_id == batch_id)

    return (
        query.order_by(DataQualityIssue.detected_at.desc()).offset(skip).limit(limit).all()
    )


@router.get("/summary", response_model=IssueSummary)
def issues_summary(db: Session = Depends(get_db), _user=Depends(get_current_user)) -> IssueSummary:
    by_status = dict(db.query(DataQualityIssue.status, func.count()).group_by(DataQualityIssue.status).all())
    by_severity = dict(db.query(DataQualityIssue.severity, func.count()).group_by(DataQualityIssue.severity).all())
    by_rule = dict(db.query(DataQualityIssue.rule_code, func.count()).group_by(DataQualityIssue.rule_code).all())

    return IssueSummary(
        by_status={k.value: v for k, v in by_status.items()},
        by_severity={k.value: v for k, v in by_severity.items()},
        by_rule_code=by_rule,
    )


@router.patch("/{issue_id}", response_model=DataQualityIssueRead)
def update_issue_status(
    issue_id: int,
    payload: IssueStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.FINANCE_MANAGER, UserRole.ANALYST)),
) -> DataQualityIssueRead:
    issue = db.get(DataQualityIssue, issue_id)
    if issue is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")

    issue.status = payload.status
    if payload.status == IssueStatus.RESOLVED:
        issue.resolved_by_id = user.id
        issue.resolved_at = datetime.now(timezone.utc)

    log_action(db, user.id, f"issue_status_changed_to_{payload.status.value}", "data_quality_issue", str(issue_id))
    db.commit()
    db.refresh(issue)
    return issue
