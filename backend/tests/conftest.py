import re
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.enums import ApprovalStatus, IssueSeverity, UserRole
from app.models.ingestion import CleanTransaction, IngestionBatch
from app.models.org import BusinessEntity, CostCenter, Department, Region
from app.models.quality import DataQualityRule
from app.models.user import User
from app.models.vendor import Category, Vendor

_settings = get_settings()
TEST_DATABASE_URL = re.sub(r"/[^/]+$", "/finops_test", _settings.database_url)

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine)

CLEANING_RULE_CODES = [
    "DUPLICATE_RECORD_ID",
    "MISSING_DATE",
    "MISSING_VENDOR",
    "INVALID_AMOUNT",
    "NEGATIVE_AMOUNT",
    "UNKNOWN_VENDOR",
    "UNKNOWN_COST_CENTER",
]


@pytest.fixture(scope="session", autouse=True)
def _schema():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def _truncate_all():
    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        _truncate_all()


@pytest.fixture
def client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def business_entity(db_session):
    entity = BusinessEntity(name="FinOps HQ", legal_name="FinOps HQ Ltd", country="Israel", base_currency="USD")
    db_session.add(entity)
    db_session.flush()
    return entity


@pytest.fixture
def region(db_session):
    r = Region(code="IL", name="Israel")
    db_session.add(r)
    db_session.flush()
    return r


@pytest.fixture
def department(db_session, business_entity):
    dept = Department(name="Engineering", business_entity_id=business_entity.id)
    db_session.add(dept)
    db_session.flush()
    return dept


@pytest.fixture
def cost_center(db_session, department):
    cc = CostCenter(code="CC-100", name="Engineering Core", department_id=department.id)
    db_session.add(cc)
    db_session.flush()
    return cc


@pytest.fixture
def category(db_session):
    cat = Category(name="Cloud Infrastructure")
    db_session.add(cat)
    db_session.flush()
    return cat


@pytest.fixture
def vendor(db_session, category):
    v = Vendor(name="Amazon Web Services", default_category_id=category.id, contract_type="annual")
    db_session.add(v)
    db_session.flush()
    return v


@pytest.fixture
def cleaning_rules(db_session):
    rules = {}
    for code in CLEANING_RULE_CODES:
        rule = DataQualityRule(
            code=code,
            name=code.replace("_", " ").title(),
            description=None,
            rule_type="validation",
            severity=IssueSeverity.HIGH,
            is_active=True,
        )
        db_session.add(rule)
        rules[code] = rule
    db_session.flush()
    return rules


def make_user(db_session, email: str, role: UserRole, password: str = "Test1234!") -> User:
    user = User(email=email, hashed_password=hash_password(password), full_name=email.split("@")[0], role=role)
    db_session.add(user)
    db_session.flush()
    return user


def auth_headers(user: User) -> dict:
    token = create_access_token(subject=user.email, role=user.role.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_user(db_session):
    return make_user(db_session, "admin@test.io", UserRole.ADMIN)


@pytest.fixture
def analyst_user(db_session):
    return make_user(db_session, "analyst@test.io", UserRole.ANALYST)


@pytest.fixture
def batch(db_session, admin_user):
    b = IngestionBatch(file_name="fixture_batch.csv", uploaded_by_id=admin_user.id)
    db_session.add(b)
    db_session.flush()
    return b


@pytest.fixture
def make_clean_transaction(db_session, batch):
    counter = {"n": 0}

    def _make(
        *,
        vendor_id: int | None = None,
        category_id: int | None = None,
        cost_center_id: int | None = None,
        department_id: int | None = None,
        business_entity_id: int | None = None,
        transaction_date: date = date(2025, 6, 1),
        total_amount: float = 100.0,
        total_amount_base_currency: float | None = None,
        currency: str = "USD",
        approval_status: ApprovalStatus = ApprovalStatus.APPROVED,
        batch_id: int | None = None,
    ) -> CleanTransaction:
        counter["n"] += 1
        tx = CleanTransaction(
            batch_id=batch_id if batch_id is not None else batch.id,
            record_id=f"TX-TEST-{counter['n']:04d}",
            vendor_id=vendor_id,
            category_id=category_id,
            cost_center_id=cost_center_id,
            department_id=department_id,
            business_entity_id=business_entity_id,
            transaction_date=transaction_date,
            currency=currency,
            net_amount=total_amount,
            tax_amount=0,
            total_amount=total_amount,
            total_amount_base_currency=total_amount_base_currency if total_amount_base_currency is not None else total_amount,
            approval_status=approval_status,
        )
        db_session.add(tx)
        db_session.flush()
        return tx

    return _make
