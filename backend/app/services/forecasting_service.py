from datetime import date

import numpy as np
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.ingestion import CleanTransaction

MIN_HISTORY_MONTHS = 6


def _month_add(d: date, n: int) -> date:
    month_index = d.month - 1 + n
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 1)


def forecast_category_spend(db: Session, category_id: int | None, months_ahead: int = 3) -> dict:
    """Projects future spend via ordinary least-squares linear regression on monthly
    totals -- classical statistical extrapolation, not a trained ML model, per the
    project's stated scope. Includes an 80% confidence band from residual std error."""
    query = db.query(
        func.date_trunc("month", CleanTransaction.transaction_date).label("period_month"),
        func.sum(CleanTransaction.total_amount_base_currency).label("total"),
    ).filter(CleanTransaction.total_amount_base_currency.isnot(None))

    if category_id is not None:
        query = query.filter(CleanTransaction.category_id == category_id)

    rows = sorted(query.group_by("period_month").all(), key=lambda r: r[0])
    history = [{"period_month": period.date(), "actual": float(total)} for period, total in rows]

    if len(history) < MIN_HISTORY_MONTHS:
        return {"history": history, "forecast": [], "note": "Not enough history for a reliable forecast"}

    x = np.arange(len(history))
    y = np.array([h["actual"] for h in history])
    slope, intercept = np.polyfit(x, y, 1)

    predicted = slope * x + intercept
    residual_std = float(np.std(y - predicted))
    band = 1.28 * residual_std  # ~80% confidence assuming normally distributed residuals

    last_month = history[-1]["period_month"]
    forecast = []
    for step in range(1, months_ahead + 1):
        x_future = len(history) - 1 + step
        point_estimate = slope * x_future + intercept
        forecast.append(
            {
                "period_month": _month_add(last_month, step),
                "forecast": round(max(point_estimate, 0), 2),
                "lower_bound": round(max(point_estimate - band, 0), 2),
                "upper_bound": round(point_estimate + band, 2),
            }
        )

    return {
        "history": history,
        "forecast": forecast,
        "trend_slope_per_month": round(float(slope), 2),
    }
