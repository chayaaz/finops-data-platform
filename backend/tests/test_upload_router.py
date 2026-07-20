import io

from app.models.enums import UserRole
from tests.conftest import auth_headers, make_user

CSV_HEADER = "record_id,vendor_name,transaction_date,currency,net_amount,tax_amount,total_amount\n"


def _csv_file(content: str, filename: str = "upload.csv"):
    return {"file": (filename, io.BytesIO(content.encode()), "text/csv")}


def test_upload_accepts_valid_csv_and_runs_cleaning_pipeline(client, admin_user, vendor, cleaning_rules):
    content = CSV_HEADER + "TX-1,Amazon Web Services,2025-06-15,USD,100,0,100\n"

    response = client.post("/upload", files=_csv_file(content), headers=auth_headers(admin_user))

    assert response.status_code == 200
    body = response.json()
    assert body["row_count"] == 1
    assert body["accepted_count"] == 1
    assert body["rejected_count"] == 0
    assert body["status"] == "completed"


def test_upload_rejects_file_missing_required_columns(client, admin_user, cleaning_rules):
    response = client.post(
        "/upload",
        files=_csv_file("foo,bar\n1,2\n"),
        headers=auth_headers(admin_user),
    )
    assert response.status_code == 400


def test_upload_rejects_unsupported_file_extension(client, admin_user):
    response = client.post(
        "/upload",
        files={"file": ("upload.txt", io.BytesIO(b"hello"), "text/plain")},
        headers=auth_headers(admin_user),
    )
    assert response.status_code == 400


def test_upload_rejects_empty_file(client, admin_user, cleaning_rules):
    response = client.post("/upload", files=_csv_file(CSV_HEADER), headers=auth_headers(admin_user))
    assert response.status_code == 400


def test_upload_is_forbidden_for_auditor_role(client, db_session, cleaning_rules):
    auditor = make_user(db_session, "auditor2@test.io", UserRole.AUDITOR)
    content = CSV_HEADER + "TX-1,Amazon Web Services,2025-06-15,USD,100,0,100\n"

    response = client.post("/upload", files=_csv_file(content), headers=auth_headers(auditor))
    assert response.status_code == 403


def test_upload_requires_authentication(client):
    content = CSV_HEADER + "TX-1,Amazon Web Services,2025-06-15,USD,100,0,100\n"
    response = client.post("/upload", files=_csv_file(content))
    assert response.status_code == 401
