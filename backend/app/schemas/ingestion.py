from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import IngestionStatus


class IngestionBatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_name: str
    uploaded_at: datetime
    status: IngestionStatus
    row_count: int
    accepted_count: int
    rejected_count: int
