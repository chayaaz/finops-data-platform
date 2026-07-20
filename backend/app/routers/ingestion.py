from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user
from app.models.ingestion import IngestionBatch
from app.schemas.ingestion import IngestionBatchRead

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.get("/batches", response_model=list[IngestionBatchRead])
def list_batches(
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
) -> list[IngestionBatchRead]:
    return db.query(IngestionBatch).order_by(IngestionBatch.uploaded_at.desc()).offset(skip).limit(limit).all()


@router.get("/batches/{batch_id}", response_model=IngestionBatchRead)
def get_batch(batch_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)) -> IngestionBatchRead:
    batch = db.get(IngestionBatch, batch_id)
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    return batch
