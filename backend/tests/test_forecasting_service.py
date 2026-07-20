from datetime import date

from app.services import forecasting_service


def test_month_add_rolls_over_year_boundary():
    assert forecasting_service._month_add(date(2025, 11, 1), 1) == date(2025, 12, 1)
    assert forecasting_service._month_add(date(2025, 11, 1), 2) == date(2026, 1, 1)


def test_forecast_reports_insufficient_history_below_minimum_months(
    db_session, category, make_clean_transaction
):
    for month in range(1, 4):
        make_clean_transaction(category_id=category.id, transaction_date=date(2025, month, 15), total_amount_base_currency=100)

    result = forecasting_service.forecast_category_spend(db_session, category.id, months_ahead=3)

    assert result["forecast"] == []
    assert "Not enough history" in result["note"]


def test_forecast_projects_a_clear_linear_trend(db_session, category, make_clean_transaction):
    # Perfectly linear growth: 100, 200, ..., 800 across 8 months.
    for month in range(1, 9):
        make_clean_transaction(
            category_id=category.id, transaction_date=date(2025, month, 15), total_amount_base_currency=100 * month
        )

    result = forecasting_service.forecast_category_spend(db_session, category.id, months_ahead=2)

    assert len(result["history"]) == 8
    assert result["trend_slope_per_month"] == 100.0
    assert len(result["forecast"]) == 2

    first_forecast = result["forecast"][0]
    assert first_forecast["period_month"] == date(2025, 9, 1)
    assert first_forecast["forecast"] == 900.0
    assert first_forecast["lower_bound"] <= first_forecast["forecast"] <= first_forecast["upper_bound"]


def test_forecast_clamps_negative_projections_to_zero(db_session, category, make_clean_transaction):
    # Steeply declining trend that would go negative if left unclamped.
    for month in range(1, 7):
        amount = max(600 - 150 * (month - 1), 1)
        make_clean_transaction(category_id=category.id, transaction_date=date(2025, month, 15), total_amount_base_currency=amount)

    result = forecasting_service.forecast_category_spend(db_session, category.id, months_ahead=3)

    for point in result["forecast"]:
        assert point["forecast"] >= 0
        assert point["lower_bound"] >= 0
