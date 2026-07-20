from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import IssueSeverity, IssueStatus


class DataQualityIssueRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_id: int
    raw_transaction_id: int | None
    clean_transaction_id: int | None
    rule_code: str
    severity: IssueSeverity
    description: str
    status: IssueStatus
    detected_at: datetime
    resolved_by_id: int | None
    resolved_at: datetime | None


class IssueStatusUpdate(BaseModel):
    status: IssueStatus


class IssueSummary(BaseModel):
    by_status: dict[str, int]
    by_severity: dict[str, int]
    by_rule_code: dict[str, int]
