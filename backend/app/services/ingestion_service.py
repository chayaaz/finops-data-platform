import io
from datetime import date

import pandas as pd
from sqlalchemy.orm import Session

from app.models.enums import IngestionStatus
from app.models.ingestion import IngestionBatch, RawTransaction

REQUIRED_COLUMNS = {"vendor_name", "transaction_date", "total_amount"}


def parse_upload(file_bytes: bytes, filename: str) -> pd.DataFrame:
    if filename.lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(io.BytesIO(file_bytes), dtype=str)
    else:
        df = pd.read_csv(io.BytesIO(file_bytes), dtype=str)

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    return df.where(pd.notnull(df), None)


def stage_raw_transactions(db: Session, uploaded_by_id: int, filename: str, df: pd.DataFrame) -> IngestionBatch:
    batch = IngestionBatch(
        file_name=filename,
        uploaded_by_id=uploaded_by_id,
        status=IngestionStatus.PROCESSING,
        row_count=len(df),
    )
    db.add(batch)
    db.flush()

    for idx, row in enumerate(df.to_dict(orient="records")):
        record_id = row.get("record_id") or f"UP-{batch.id}-{idx + 1:05d}"
        db.add(
            RawTransaction(
                batch_id=batch.id,
                record_id=record_id,
                source_file_name=row.get("source_file_name") or filename,
                load_date=row.get("load_date") or date.today().isoformat(),
                transaction_date=row.get("transaction_date"),
                posting_date=row.get("posting_date"),
                invoice_number=row.get("invoice_number"),
                vendor_name=row.get("vendor_name"),
                department=row.get("department"),
                cost_center=row.get("cost_center"),
                category=row.get("category"),
                item_type=row.get("item_type"),
                description=row.get("description"),
                quantity=row.get("quantity"),
                unit_of_measure=row.get("unit_of_measure"),
                currency=row.get("currency"),
                net_amount=row.get("net_amount"),
                tax_amount=row.get("tax_amount"),
                total_amount=row.get("total_amount"),
                payment_method=row.get("payment_method"),
                approval_status=row.get("approval_status"),
                business_entity=row.get("business_entity"),
                region=row.get("region"),
                created_by=row.get("created_by"),
                notes=row.get("notes"),
            )
        )

    return batch
