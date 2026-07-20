from app.models.enums import UserRole
from tests.conftest import auth_headers, make_user


def test_admin_can_list_users(client, admin_user):
    response = client.get("/admin/users", headers=auth_headers(admin_user))
    assert response.status_code == 200


def test_analyst_cannot_list_users(client, analyst_user):
    response = client.get("/admin/users", headers=auth_headers(analyst_user))
    assert response.status_code == 403


def test_auditor_cannot_create_budgets(client, db_session, cost_center):
    auditor = make_user(db_session, "auditor@test.io", UserRole.AUDITOR)
    payload = {
        "cost_center_id": cost_center.id,
        "category_id": None,
        "period_month": "2025-06-01",
        "currency": "USD",
        "budget_amount": 1000,
    }
    response = client.post("/budgets", json=payload, headers=auth_headers(auditor))
    assert response.status_code == 403


def test_finance_manager_can_create_budgets(client, db_session, cost_center):
    manager = make_user(db_session, "manager@test.io", UserRole.FINANCE_MANAGER)
    payload = {
        "cost_center_id": cost_center.id,
        "category_id": None,
        "period_month": "2025-06-01",
        "currency": "USD",
        "budget_amount": 1000,
    }
    response = client.post("/budgets", json=payload, headers=auth_headers(manager))
    assert response.status_code == 200
    assert response.json()["budget_amount"] == 1000
