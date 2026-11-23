from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user, require_roles
from app.models.enums import IssueStatus, UserRole
from app.models.ingestion import CleanTransaction, RawTransaction
from app.models.quality import DataQualityIssue
from app.models.user import User
from app.schemas.issue import (
    DataQualityIssueRead,
    IssueStatusUpdate,
    IssueSummary,
    RawRowFix,
    RawRowFixResult,
    RawRowRead,
)
from app.services import cleaning_service
from app.services.audit_service import log_action

router = APIRouter(prefix="/issues", tags=["issues"])

_can_edit_issues = require_roles(UserRole.ADMIN, UserRole.FINANCE_MANAGER, UserRole.ANALYST)


def _raw_row_for_issue(db: Session, issue_id: int) -> RawTransaction:
    issue = db.get(DataQualityIssue, issue_id)
    if issue is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")
    if issue.raw_transaction_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This issue has no source row to fix")
    return db.get(RawTransaction, issue.raw_transaction_id)


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
def issues_summary(
    db: Session = Depends(get_db), _user=Depends(get_current_user), batch_id: int | None = None
) -> IssueSummary:
    def grouped(column):
        query = db.query(column, func.count())
        if batch_id is not None:
            query = query.filter(DataQualityIssue.batch_id == batch_id)
        return dict(query.group_by(column).all())

    by_status = grouped(DataQualityIssue.status)
    by_severity = grouped(DataQualityIssue.severity)
    by_rule = grouped(DataQualityIssue.rule_code)

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
    user: User = Depends(_can_edit_issues),
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


@router.get("/{issue_id}/raw-row", response_model=RawRowRead)
def get_issue_raw_row(issue_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)) -> RawRowRead:
    raw = _raw_row_for_issue(db, issue_id)
    is_accepted = (
        db.query(CleanTransaction.id).filter(CleanTransaction.raw_transaction_id == raw.id).first() is not None
    )
    row = RawRowRead.model_validate(raw)
    row.is_accepted = is_accepted
    return row


@router.post("/{issue_id}/fix", response_model=RawRowFixResult)
def fix_issue_row(
    issue_id: int,
    payload: RawRowFix,
    db: Session = Depends(get_db),
    user: User = Depends(_can_edit_issues),
) -> RawRowFixResult:
    raw = _raw_row_for_issue(db, issue_id)
    was_accepted = (
        db.query(CleanTransaction.id).filter(CleanTransaction.raw_transaction_id == raw.id).first() is not None
    )

    try:
        # Savepoint: if the corrected row is still invalid, only this attempt is undone.
        with db.begin_nested():
            result = cleaning_service.fix_raw_row(db, raw, payload.model_dump(exclude_unset=True), user.id)
    except cleaning_service.RowStillInvalidError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Row still cannot be accepted: {exc}"
        ) from exc

    db.flush()
    log_action(
        db, user.id, "issue_row_fixed", "data_quality_issue", str(issue_id),
        details=f"record_id={result.clean.record_id}; added={not was_accepted}",
    )
    db.commit()
    return RawRowFixResult(
        clean_transaction_id=result.clean.id,
        was_added=not was_accepted,
        remaining_problems=[description for _, description in result.problems],
    )
