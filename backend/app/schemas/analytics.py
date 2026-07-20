from datetime import date

from pydantic import BaseModel


class DashboardKpis(BaseModel):
    total_spend: float
    total_transactions: int
    open_issues: int
    open_anomalies: int
    data_quality_score_pct: float
    mom_growth_pct: float | None
    top_category_name: str | None
    top_category_spend: float | None


class TrendPoint(BaseModel):
    period_month: date
    total_spend: float


class ForecastPoint(BaseModel):
    period_month: date
    forecast: float
    lower_bound: float
    upper_bound: float


class ForecastResult(BaseModel):
    history: list[dict]
    forecast: list[ForecastPoint]
    trend_slope_per_month: float | None = None
    note: str | None = None


class AllocationRow(BaseModel):
    department_id: int
    department_name: str
    weight_pct: float
    allocated_amount: float


class FxExposureRow(BaseModel):
    currency: str
    total_base_currency: float
    share_pct: float
    transaction_count: int
