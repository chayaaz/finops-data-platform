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


class RawRowRead(BaseModel):
    """The editable source fields of the raw row behind an issue."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_id: int
    record_id: str
    transaction_date: str | None
    vendor_name: str | None
    department: str | None
    cost_center: str | None
    category: str | None
    currency: str | None
    net_amount: str | None
    tax_amount: str | None
    total_amount: str | None
    business_entity: str | None
    is_accepted: bool = False


class RawRowFix(BaseModel):
    record_id: str | None = None
    transaction_date: str | None = None
    vendor_name: str | None = None
    department: str | None = None
    cost_center: str | None = None
    category: str | None = None
    currency: str | None = None
    net_amount: str | None = None
    tax_amount: str | None = None
    total_amount: str | None = None
    business_entity: str | None = None


class RawRowFixResult(BaseModel):
    clean_transaction_id: int
    was_added: bool
    remaining_problems: list[str]
