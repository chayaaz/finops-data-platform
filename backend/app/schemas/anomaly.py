from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import AnomalyStatus


class AnomalyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    clean_transaction_id: int
    anomaly_type: str
    z_score: float | None
    detail: str | None
    status: AnomalyStatus
    detected_at: datetime
    reviewed_by_id: int | None
    reviewed_at: datetime | None


class AnomalyStatusUpdate(BaseModel):
    status: AnomalyStatus


class BenfordGroupResult(BaseModel):
    group_id: int
    sample_size: int
    chi_square: float
    observed_distribution: dict[int, float]
    expected_distribution: dict[int, float]
    flagged: bool
