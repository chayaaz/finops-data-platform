from datetime import date

from pydantic import BaseModel, ConfigDict

from app.models.enums import ApprovalStatus


class CleanTransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    record_id: str
    transaction_date: date
    posting_date: date | None
    invoice_number: str | None
    vendor_id: int | None
    department_id: int | None
    cost_center_id: int | None
    category_id: int | None
    business_entity_id: int | None
    region_id: int | None
    currency: str
    net_amount: float
    tax_amount: float
    total_amount: float
    total_amount_base_currency: float | None
    payment_method: str | None
    approval_status: ApprovalStatus
    description: str | None


class TransactionPage(BaseModel):
    items: list[CleanTransactionRead]
    total: int
    skip: int
    limit: int


class RawTransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_id: int
    record_id: str
    vendor_name: str | None
    department: str | None
    cost_center: str | None
    category: str | None
    transaction_date: str | None
    currency: str | None
    total_amount: str | None
