from datetime import date

from pydantic import BaseModel, ConfigDict


class VendorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    default_category_id: int | None
    contract_type: str | None
    is_active: bool


class VendorShare(BaseModel):
    vendor_id: int
    vendor_name: str
    spend: float
    share_pct: float


class VendorConcentration(BaseModel):
    hhi: float
    risk_level: str
    total_spend: float | None = None
    vendor_shares: list[VendorShare]


class CommitmentUtilization(BaseModel):
    vendor_id: int
    vendor_name: str
    business_entity_id: int
    business_entity_name: str
    period_month: date
    currency: str
    committed_amount: float
    utilized_amount: float
    utilization_pct: float
