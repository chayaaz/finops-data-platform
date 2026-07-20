from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ApprovalStatus, IngestionStatus
from app.models.org import BusinessEntity, CostCenter, Department, Region
from app.models.user import User
from app.models.vendor import Category, Vendor


class IngestionBatch(Base):
    __tablename__ = "ingestion_batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    file_name: Mapped[str] = mapped_column(String(255))
    uploaded_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    status: Mapped[IngestionStatus] = mapped_column(
        Enum(IngestionStatus, name="ingestion_status"), default=IngestionStatus.PROCESSING
    )
    row_count: Mapped[int] = mapped_column(default=0)
    accepted_count: Mapped[int] = mapped_column(default=0)
    rejected_count: Mapped[int] = mapped_column(default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    uploaded_by: Mapped[User] = relationship()


class RawTransaction(Base):
    """Staging table mirroring the uploaded file columns verbatim, before any normalization."""

    __tablename__ = "raw_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("ingestion_batches.id"), index=True)
    record_id: Mapped[str] = mapped_column(String(50), index=True)
    source_file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    load_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    transaction_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    posting_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    invoice_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    vendor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cost_center: Mapped[str | None] = mapped_column(String(50), nullable=True)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    item_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    quantity: Mapped[str | None] = mapped_column(String(50), nullable=True)
    unit_of_measure: Mapped[str | None] = mapped_column(String(50), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(20), nullable=True)
    net_amount: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tax_amount: Mapped[str | None] = mapped_column(String(50), nullable=True)
    total_amount: Mapped[str | None] = mapped_column(String(50), nullable=True)
    payment_method: Mapped[str | None] = mapped_column(String(100), nullable=True)
    approval_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    business_entity: Mapped[str | None] = mapped_column(String(255), nullable=True)
    region: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    batch: Mapped[IngestionBatch] = relationship()


class CleanTransaction(Base):
    __tablename__ = "clean_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    raw_transaction_id: Mapped[int | None] = mapped_column(ForeignKey("raw_transactions.id"), nullable=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("ingestion_batches.id"), index=True)
    record_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)

    vendor_id: Mapped[int | None] = mapped_column(ForeignKey("vendors.id"), nullable=True)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"), nullable=True)
    cost_center_id: Mapped[int | None] = mapped_column(ForeignKey("cost_centers.id"), nullable=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    business_entity_id: Mapped[int | None] = mapped_column(ForeignKey("business_entities.id"), nullable=True)
    region_id: Mapped[int | None] = mapped_column(ForeignKey("regions.id"), nullable=True)

    invoice_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    transaction_date: Mapped[date] = mapped_column(Date, index=True)
    posting_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    item_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    quantity: Mapped[float | None] = mapped_column(Numeric(14, 4), nullable=True)
    unit_of_measure: Mapped[str | None] = mapped_column(String(50), nullable=True)

    currency: Mapped[str] = mapped_column(String(3))
    net_amount: Mapped[float] = mapped_column(Numeric(14, 2))
    tax_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    total_amount: Mapped[float] = mapped_column(Numeric(14, 2))
    total_amount_base_currency: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)

    payment_method: Mapped[str | None] = mapped_column(String(100), nullable=True)
    approval_status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus, name="approval_status"), default=ApprovalStatus.PENDING
    )
    created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    vendor: Mapped[Vendor | None] = relationship()
    department: Mapped[Department | None] = relationship()
    cost_center: Mapped[CostCenter | None] = relationship()
    category: Mapped[Category | None] = relationship()
    business_entity: Mapped[BusinessEntity | None] = relationship()
    region: Mapped[Region | None] = relationship()
    batch: Mapped[IngestionBatch] = relationship()
