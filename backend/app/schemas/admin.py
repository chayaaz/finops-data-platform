from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import IssueSeverity


class DataQualityRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: str | None
    rule_type: str
    severity: IssueSeverity
    threshold: float | None
    is_active: bool


class DataQualityRuleUpdate(BaseModel):
    severity: IssueSeverity | None = None
    threshold: float | None = None
    is_active: bool | None = None


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    action: str
    entity_type: str
    entity_id: str | None
    details: str | None
    created_at: datetime


class IngestionBatchDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_name: str
    uploaded_by_id: int
    uploaded_at: datetime
    status: str
    row_count: int
    accepted_count: int
    rejected_count: int
