"""Runs the cleaning/anomaly pipeline over every ingestion batch that hasn't been processed yet."""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.db.session import SessionLocal  # noqa: E402
from app.models.ingestion import CleanTransaction, IngestionBatch  # noqa: E402
from app.services import cleaning_service  # noqa: E402


def main() -> None:
    db = SessionLocal()
    try:
        processed_batch_ids = {row[0] for row in db.query(CleanTransaction.batch_id).distinct().all()}
        batches = (
            db.query(IngestionBatch)
            .filter(~IngestionBatch.id.in_(processed_batch_ids) if processed_batch_ids else True)
            .order_by(IngestionBatch.id)
            .all()
        )

        for batch in batches:
            cleaning_service.process_batch(db, batch)
            db.commit()
            print(f"  {batch.file_name}: accepted={batch.accepted_count} rejected={batch.rejected_count}")

        print(f"Processed {len(batches)} batches.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
