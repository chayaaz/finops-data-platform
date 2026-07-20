"""Loads the generated synthetic dataset (data_generator/output/) into Postgres.

Assumes `alembic upgrade head` has already been run. Resets all tables first,
so it is safe to re-run whenever the generator output changes.
"""

import csv
import glob
import sys
from datetime import date
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(PROJECT_ROOT / "data_generator"))

from sqlalchemy import text  # noqa: E402

import app.models as m  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.models.enums import IngestionStatus  # noqa: E402
from reference_data import BUSINESS_ENTITIES, CATEGORY_TREE, REGIONS, VENDORS  # noqa: E402

DATA_DIR = PROJECT_ROOT / "data_generator" / "output"
RAW_DIR = DATA_DIR / "raw"

DATA_QUALITY_RULES = [
    ("DUPLICATE_RECORD_ID", "Duplicate record ID", "duplicate", "high"),
    ("MISSING_VENDOR", "Vendor name is missing", "missing_field", "medium"),
    ("MISSING_DATE", "Transaction date is missing or invalid", "missing_field", "high"),
    ("INVALID_AMOUNT", "Total amount is less than net amount", "invalid_value", "high"),
    ("NEGATIVE_AMOUNT", "Total amount is negative", "invalid_value", "critical"),
    ("UNKNOWN_VENDOR", "Vendor name not found in vendor master data", "referential", "medium"),
    ("UNKNOWN_COST_CENTER", "Cost center not found in master data", "referential", "medium"),
]


def reset_database() -> None:
    table_names = ", ".join(f'"{t.name}"' for t in Base.metadata.sorted_tables)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {table_names} RESTART IDENTITY CASCADE;"))


def seed_business_entities(db) -> dict[str, m.BusinessEntity]:
    entity_by_name = {}
    for e in BUSINESS_ENTITIES:
        obj = m.BusinessEntity(
            name=e["name"], legal_name=e["legal_name"], country=e["country"], base_currency=e["base_currency"]
        )
        db.add(obj)
        entity_by_name[e["name"]] = obj
    db.flush()
    return entity_by_name


def seed_regions(db) -> None:
    for code, name in REGIONS:
        db.add(m.Region(code=code, name=name))
    db.flush()


def seed_categories(db) -> dict[str, m.Category]:
    category_by_name = {}
    for parent_name, children in CATEGORY_TREE.items():
        parent = m.Category(name=parent_name, parent_category_id=None)
        db.add(parent)
        db.flush()
        category_by_name[parent_name] = parent
        for child_name, _lo, _hi in children:
            child = m.Category(name=child_name, parent_category_id=parent.id)
            db.add(child)
            category_by_name[child_name] = child
    db.flush()
    return category_by_name


def seed_vendors(db, category_by_name: dict[str, m.Category]) -> dict[str, m.Vendor]:
    vendor_by_name = {}
    for vendor_name, (default_category, contract_type) in VENDORS.items():
        obj = m.Vendor(
            name=vendor_name,
            default_category_id=category_by_name[default_category].id,
            contract_type=contract_type,
        )
        db.add(obj)
        vendor_by_name[vendor_name] = obj
    db.flush()
    return vendor_by_name


def seed_departments_and_cost_centers(
    db, entity_by_name: dict[str, m.BusinessEntity]
) -> dict[str, m.CostCenter]:
    combos = set()
    for path in sorted(glob.glob(str(RAW_DIR / "*.csv"))):
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                combos.add((row["business_entity"], row["department"], row["cost_center"]))

    dept_by_key: dict[tuple[str, str], m.Department] = {}
    cost_center_by_code: dict[str, m.CostCenter] = {}
    for entity_name, dept_name, cc_code in sorted(combos):
        if entity_name not in entity_by_name:
            continue
        dept_key = (entity_name, dept_name)
        if dept_key not in dept_by_key:
            dept = m.Department(name=dept_name, business_entity_id=entity_by_name[entity_name].id)
            db.add(dept)
            db.flush()
            dept_by_key[dept_key] = dept
        if cc_code not in cost_center_by_code:
            cc = m.CostCenter(code=cc_code, name=f"{dept_name} - {cc_code}", department_id=dept_by_key[dept_key].id)
            db.add(cc)
            cost_center_by_code[cc_code] = cc
    db.flush()
    return cost_center_by_code


def seed_data_quality_rules(db) -> None:
    for code, name, rule_type, severity in DATA_QUALITY_RULES:
        db.add(m.DataQualityRule(code=code, name=name, description=name, rule_type=rule_type, severity=severity))
    db.flush()


def seed_users(db) -> None:
    with open(DATA_DIR / "users.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            db.add(
                m.User(
                    email=row["email"],
                    full_name=row["full_name"],
                    role=row["role"],
                    hashed_password=hash_password(row["password"]),
                )
            )
    db.flush()


def seed_exchange_rates(db) -> None:
    with open(DATA_DIR / "exchange_rates.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            db.add(
                m.ExchangeRate(
                    rate_date=date.fromisoformat(row["rate_date"]),
                    currency_code=row["currency_code"],
                    rate_to_base=float(row["rate_to_base"]),
                )
            )
    db.flush()


def seed_budgets(db, cost_center_by_code: dict[str, m.CostCenter], category_by_name: dict[str, m.Category]) -> None:
    skipped = 0
    with open(DATA_DIR / "budgets.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cc = cost_center_by_code.get(row["cost_center_code"])
            category = category_by_name.get(row["category_name"])
            if cc is None or category is None:
                skipped += 1
                continue
            db.add(
                m.Budget(
                    cost_center_id=cc.id,
                    category_id=category.id,
                    period_month=date.fromisoformat(row["period_month"]),
                    currency=row["currency"],
                    budget_amount=float(row["budget_amount"]),
                )
            )
    db.flush()
    if skipped:
        print(f"  skipped {skipped} budget rows with unresolved cost center/category")


def seed_commitments(
    db, vendor_by_name: dict[str, m.Vendor], entity_by_name: dict[str, m.BusinessEntity]
) -> None:
    with open(DATA_DIR / "commitments.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            db.add(
                m.Commitment(
                    vendor_id=vendor_by_name[row["vendor_name"]].id,
                    business_entity_id=entity_by_name[row["business_entity_name"]].id,
                    period_month=date.fromisoformat(row["period_month"]),
                    currency=row["currency"],
                    committed_amount=float(row["committed_amount"]),
                    utilized_amount=float(row["utilized_amount"]),
                )
            )
    db.flush()


def seed_raw_transactions(db, admin_user: m.User) -> int:
    total = 0
    for path in sorted(glob.glob(str(RAW_DIR / "*.csv"))):
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        batch = m.IngestionBatch(
            file_name=Path(path).name,
            uploaded_by_id=admin_user.id,
            status=IngestionStatus.COMPLETED,
            row_count=len(rows),
        )
        db.add(batch)
        db.flush()

        for row in rows:
            db.add(
                m.RawTransaction(
                    batch_id=batch.id,
                    record_id=row["record_id"],
                    source_file_name=row["source_file_name"],
                    load_date=row["load_date"],
                    transaction_date=row["transaction_date"],
                    posting_date=row["posting_date"],
                    invoice_number=row["invoice_number"],
                    vendor_name=row["vendor_name"],
                    department=row["department"],
                    cost_center=row["cost_center"],
                    category=row["category"],
                    item_type=row["item_type"],
                    description=row["description"],
                    quantity=row["quantity"],
                    unit_of_measure=row["unit_of_measure"],
                    currency=row["currency"],
                    net_amount=row["net_amount"],
                    tax_amount=row["tax_amount"],
                    total_amount=row["total_amount"],
                    payment_method=row["payment_method"],
                    approval_status=row["approval_status"],
                    business_entity=row["business_entity"],
                    region=row["region"],
                    created_by=row["created_by"],
                    notes=row["notes"],
                )
            )
        total += len(rows)
    db.flush()
    return total


def main() -> None:
    print("Resetting database...")
    reset_database()

    db = SessionLocal()
    try:
        print("Seeding business entities...")
        entity_by_name = seed_business_entities(db)
        print("Seeding regions...")
        seed_regions(db)
        print("Seeding categories...")
        category_by_name = seed_categories(db)
        print("Seeding vendors...")
        vendor_by_name = seed_vendors(db, category_by_name)
        print("Seeding departments & cost centers...")
        cost_center_by_code = seed_departments_and_cost_centers(db, entity_by_name)
        print("Seeding data quality rules...")
        seed_data_quality_rules(db)
        print("Seeding users...")
        seed_users(db)
        db.commit()

        admin_user = db.query(m.User).filter(m.User.role == "admin").one()

        print("Seeding exchange rates...")
        seed_exchange_rates(db)
        print("Seeding budgets...")
        seed_budgets(db, cost_center_by_code, category_by_name)
        print("Seeding commitments...")
        seed_commitments(db, vendor_by_name, entity_by_name)
        print("Seeding raw transactions...")
        total_raw = seed_raw_transactions(db, admin_user)
        db.commit()

        print(f"Done. Seeded {total_raw} raw transactions across all ingestion batches.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
