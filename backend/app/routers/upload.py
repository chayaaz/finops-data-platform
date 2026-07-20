from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import require_roles
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.ingestion import IngestionBatchRead
from app.services import cleaning_service, ingestion_service

router = APIRouter(prefix="/upload", tags=["upload"])

ALLOWED_EXTENSIONS = (".csv", ".xlsx", ".xls")


@router.post("", response_model=IngestionBatchRead)
def upload_transactions(
    file: UploadFile,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.FINANCE_MANAGER, UserRole.ANALYST)),
) -> IngestionBatchRead:
    if not file.filename.lower().endswith(ALLOWED_EXTENSIONS):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only CSV or Excel files are supported")

    try:
        df = ingestion_service.parse_upload(file.file.read(), file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if df.empty:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file has no data rows")

    batch = ingestion_service.stage_raw_transactions(db, user.id, file.filename, df)
    cleaning_service.process_batch(db, batch)
    db.commit()
    db.refresh(batch)
    return batch
