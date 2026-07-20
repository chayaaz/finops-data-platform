from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import AnomalyStatus, IssueSeverity, IssueStatus
from app.models.ingestion import CleanTransaction, IngestionBatch, RawTransaction
from app.models.user import User

_issue_severity_enum = Enum(IssueSeverity, name="issue_severity")


class DataQualityRule(Base):
    __tablename__ = "data_quality_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    rule_type: Mapped[str] = mapped_column(String(50))
    severity: Mapped[IssueSeverity] = mapped_column(_issue_severity_enum)
    threshold: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class DataQualityIssue(Base):
    __tablename__ = "data_quality_issues"

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("ingestion_batches.id"), index=True)
    raw_transaction_id: Mapped[int | None] = mapped_column(ForeignKey("raw_transactions.id"), nullable=True)
    clean_transaction_id: Mapped[int | None] = mapped_column(ForeignKey("clean_transactions.id"), nullable=True)
    rule_code: Mapped[str] = mapped_column(String(50), index=True)
    severity: Mapped[IssueSeverity] = mapped_column(_issue_severity_enum)
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[IssueStatus] = mapped_column(Enum(IssueStatus, name="issue_status"), default=IssueStatus.OPEN)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    batch: Mapped[IngestionBatch] = relationship()
    raw_transaction: Mapped[RawTransaction | None] = relationship()
    clean_transaction: Mapped[CleanTransaction | None] = relationship()
    resolved_by: Mapped[User | None] = relationship()


class Anomaly(Base):
    __tablename__ = "anomalies"

    id: Mapped[int] = mapped_column(primary_key=True)
    clean_transaction_id: Mapped[int] = mapped_column(ForeignKey("clean_transactions.id"), index=True)
    anomaly_type: Mapped[str] = mapped_column(String(50))
    z_score: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[AnomalyStatus] = mapped_column(Enum(AnomalyStatus, name="anomaly_status"), default=AnomalyStatus.OPEN)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reviewed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    clean_transaction: Mapped[CleanTransaction] = relationship()
    reviewed_by: Mapped[User | None] = relationship()
