from tests.conftest import auth_headers


def test_login_succeeds_with_correct_credentials(client, admin_user):
    response = client.post("/auth/login", data={"username": admin_user.email, "password": "Test1234!"})

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == admin_user.email
    assert "access_token" in body


def test_login_rejects_wrong_password(client, admin_user):
    response = client.post("/auth/login", data={"username": admin_user.email, "password": "wrong-password"})
    assert response.status_code == 401


def test_login_rejects_unknown_email(client):
    response = client.post("/auth/login", data={"username": "nobody@test.io", "password": "whatever"})
    assert response.status_code == 401


def test_login_rejects_disabled_user(client, db_session, admin_user):
    admin_user.is_active = False
    db_session.flush()

    response = client.post("/auth/login", data={"username": admin_user.email, "password": "Test1234!"})
    assert response.status_code == 403


def test_me_returns_current_user_with_valid_token(client, admin_user):
    response = client.get("/auth/me", headers=auth_headers(admin_user))
    assert response.status_code == 200
    assert response.json()["email"] == admin_user.email


def test_protected_endpoint_rejects_missing_token(client):
    response = client.get("/dimensions/categories")
    assert response.status_code == 401


def test_protected_endpoint_rejects_garbage_token(client):
    response = client.get("/dimensions/categories", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401
