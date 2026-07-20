from datetime import date

from pydantic import BaseModel, ConfigDict


class BudgetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cost_center_id: int
    category_id: int | None
    period_month: date
    currency: str
    budget_amount: float


class BudgetCreate(BaseModel):
    cost_center_id: int
    category_id: int | None = None
    period_month: date
    currency: str
    budget_amount: float


class BudgetUpdate(BaseModel):
    budget_amount: float


class BudgetVarianceRow(BaseModel):
    cost_center_id: int | None
    category_id: int | None
    period_month: date
    budget_amount: float
    actual_amount: float
    variance: float
    variance_pct: float | None
    is_over_budget: bool


class BurnDownPoint(BaseModel):
    period_month: date
    cumulative_budget: float
    cumulative_actual: float
