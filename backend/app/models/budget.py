from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.org import BusinessEntity, CostCenter
from app.models.vendor import Category, Vendor


class Budget(Base):
    __tablename__ = "budgets"
    __table_args__ = (
        UniqueConstraint("cost_center_id", "category_id", "period_month", name="uq_budget_scope_period"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    cost_center_id: Mapped[int] = mapped_column(ForeignKey("cost_centers.id"))
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    period_month: Mapped[date] = mapped_column(Date, index=True)
    currency: Mapped[str] = mapped_column(String(3))
    budget_amount: Mapped[float] = mapped_column(Numeric(14, 2))

    cost_center: Mapped[CostCenter] = relationship()
    category: Mapped[Category | None] = relationship()


class Commitment(Base):
    __tablename__ = "commitments"

    id: Mapped[int] = mapped_column(primary_key=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"))
    business_entity_id: Mapped[int] = mapped_column(ForeignKey("business_entities.id"))
    period_month: Mapped[date] = mapped_column(Date, index=True)
    currency: Mapped[str] = mapped_column(String(3))
    committed_amount: Mapped[float] = mapped_column(Numeric(14, 2))
    utilized_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0)

    vendor: Mapped[Vendor] = relationship()
    business_entity: Mapped[BusinessEntity] = relationship()
