"""Generates 36 months of realistic, deliberately messy raw transaction CSVs.

Output: one CSV per month under output/raw/, mirroring the columns a finance
team would actually export from an expense/invoicing system, matching the
shape the platform's upload endpoint expects.
"""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

from reference_data import (
    APPROVAL_STATUSES,
    BUSINESS_ENTITIES,
    CATEGORY_TREE,
    CREATED_BY_USERS,
    CURRENCY_VARIANTS,
    DEPARTMENTS,
    ITEM_TYPES,
    PAYMENT_METHOD_VARIANTS,
    REGIONS,
    UNITS_OF_MEASURE,
    VENDORS,
)

random.seed(42)

OUTPUT_DIR = Path(__file__).parent / "output" / "raw"

START_YEAR_MONTH = (2023, 1)
NUM_MONTHS = 36

VAT_RATE_BY_COUNTRY = {"Israel": 0.17, "Germany": 0.19, "United States": 0.0}

RECURRING_VENDORS = {
    "Google Cloud", "Microsoft Azure", "Amazon Web Services", "Slack Technologies",
    "Atlassian", "Salesforce", "Microsoft 365", "Google Workspace", "Okta",
    "WeWork", "ADP Payroll", "Migdal Insurance", "Datadog",
}

DESCRIPTION_TEMPLATES = {
    "Cloud Infrastructure": "Monthly cloud consumption",
    "Monitoring": "Observability platform subscription",
    "Hosting & CDN": "CDN bandwidth and hosting fees",
    "Data & Analytics Platforms": "Data warehouse compute usage",
    "SaaS Subscriptions": "Monthly SaaS license fee",
    "CRM": "CRM platform license",
    "Productivity Software": "Productivity suite license",
    "Security Software": "Security platform subscription",
    "Marketing": "Marketing campaign spend",
    "Advertising": "Digital ad spend",
    "Events & Sponsorships": "Conference sponsorship",
    "Market Research": "Market research report",
    "Travel & Meals": "Business travel expense",
    "Office Supplies": "Office supplies order",
    "Utilities": "Monthly utilities bill",
    "Facilities & Rent": "Office rent and facilities",
    "Hardware": "Hardware purchase",
    "IT Equipment": "IT equipment purchase",
    "Office Equipment": "Office furniture and equipment",
    "Legal & Compliance": "Legal advisory services",
    "Consulting": "Consulting engagement",
    "Recruiting": "Recruiting services",
    "Training & Education": "Employee training program",
    "Payroll Services": "Payroll processing fee",
    "Benefits Administration": "Employee benefits administration",
    "Insurance": "Insurance premium",
    "Shipping & Logistics": "Shipping and logistics fee",
}

CATEGORY_BY_NAME = {
    child: (parent, lo, hi)
    for parent, children in CATEGORY_TREE.items()
    for child, lo, hi in children
}


def month_sequence(start_year: int, start_month: int, count: int) -> list[tuple[int, int]]:
    months = []
    year, month = start_year, start_month
    for _ in range(count):
        months.append((year, month))
        month += 1
        if month > 12:
            month = 1
            year += 1
    return months


def random_day_in_month(year: int, month: int) -> date:
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    days_in_month = (next_month - date(year, month, 1)).days
    return date(year, month, random.randint(1, days_in_month))


def seasonal_multiplier(month: int, category: str) -> float:
    if category in ("Marketing", "Advertising", "Events & Sponsorships") and month in (11, 12):
        return 1.6
    if category == "Travel & Meals" and month in (6, 7, 8, 12):
        return 1.4
    if category == "Utilities" and month in (1, 2, 7, 8):
        return 1.2
    return 1.0


def pick_vendor_for_department(department: str) -> str:
    if department == "R&D":
        pool = ["Google Cloud", "Microsoft Azure", "Amazon Web Services", "Datadog", "New Relic",
                "Grafana Labs", "Cloudflare", "Fastly", "Snowflake", "Databricks", "Dell Technologies",
                "Apple Business", "Lenovo", "Cisco Systems", "1Password", "CrowdStrike"]
    elif department == "Marketing":
        pool = ["Meta Ads", "Google Ads", "LinkedIn Marketing", "Mailchimp", "Hootsuite",
                "Nielsen Research", "Gartner", "HubSpot"]
    elif department == "Sales":
        pool = ["Salesforce", "HubSpot", "Pipedrive", "LinkedIn Marketing", "Booking.com Business",
                "Uber for Business", "Delta Airlines"]
    elif department == "HR":
        pool = ["ADP Payroll", "Migdal Insurance", "LinkedIn Talent Solutions", "Udemy Business",
                "Coursera for Business", "Herman Miller"]
    elif department == "IT":
        pool = ["Microsoft 365", "Google Workspace", "Okta", "CrowdStrike", "1Password",
                "Dell Technologies", "Cisco Systems", "Apple Business", "Adobe"]
    elif department == "Finance":
        pool = ["Deloitte Consulting", "Herzog Fox & Neeman", "ADP Payroll", "McKinsey & Company"]
    elif department == "Customer Success":
        pool = ["Zoom Video", "Salesforce", "Slack Technologies", "Atlassian"]
    else:  # Operations
        pool = ["WeWork", "Regus", "Israel Electric Corp", "E.ON Energy", "DHL Express", "FedEx",
                "Staples", "Amazon Business"]
    return random.choice(pool)


def dirty_currency(canonical: str) -> str:
    if random.random() < 0.12:
        return random.choice(CURRENCY_VARIANTS[canonical])
    return canonical


def dirty_payment_method(canonical: str) -> str:
    if random.random() < 0.15:
        return random.choice(PAYMENT_METHOD_VARIANTS[canonical])
    return canonical


def maybe_pad_whitespace(text: str) -> str:
    if random.random() < 0.05:
        return f"  {text}  "
    return text


def build_row(
    record_seq: int,
    year: int,
    month: int,
    entity: dict,
    dept_name: str,
    cost_center_code: str,
    vendor_name: str | None = None,
) -> dict:
    vendor_name = vendor_name or pick_vendor_for_department(dept_name)
    category, contract_type = VENDORS[vendor_name]
    _parent_category, lo, hi = CATEGORY_BY_NAME[category]

    multiplier = seasonal_multiplier(month, category)
    net_amount = round(random.uniform(lo, hi) * multiplier, 2)

    vat_rate = VAT_RATE_BY_COUNTRY.get(entity["country"], 0.0)
    tax_amount = round(net_amount * vat_rate, 2)
    total_amount = round(net_amount + tax_amount, 2)

    currency = {"Israel": "ILS", "Germany": "EUR", "United States": "USD"}[entity["country"]]

    tx_date = random_day_in_month(year, month)
    posting_date = tx_date + timedelta(days=random.randint(1, 10))
    load_date = date(year, month, 28) if month != 12 else date(year, 12, 30)

    region = random.choice(REGIONS)[0]
    payment_method = "Corporate Card" if contract_type == "Ad-Hoc" else random.choice(
        ["Direct Debit", "Wire Transfer", "Bank Transfer", "Credit Card"]
    )
    approval_status = random.choices(APPROVAL_STATUSES, weights=[10, 25, 60, 5])[0]

    row = {
        "record_id": f"TX-{year}{month:02d}-{record_seq:04d}",
        "source_file_id": f"F{year}{month:02d}",
        "source_file_name": f"finops_upload_{year}_{month:02d}.csv",
        "load_date": load_date.isoformat(),
        "transaction_date": tx_date.isoformat(),
        "posting_date": posting_date.isoformat(),
        "invoice_number": f"INV-{month:02d}-{random.randint(10000, 99999)}",
        "vendor_name": maybe_pad_whitespace(vendor_name),
        "department": dept_name,
        "cost_center": cost_center_code,
        "category": category,
        "item_type": random.choice(ITEM_TYPES),
        "description": DESCRIPTION_TEMPLATES.get(category, "General expense"),
        "quantity": round(random.uniform(1, 200), 2),
        "unit_of_measure": random.choice(UNITS_OF_MEASURE),
        "currency": dirty_currency(currency),
        "net_amount": net_amount,
        "tax_amount": tax_amount,
        "total_amount": total_amount,
        "payment_method": dirty_payment_method(payment_method),
        "approval_status": approval_status,
        "business_entity": entity["name"],
        "region": region,
        "created_by": random.choice(CREATED_BY_USERS),
        "notes": "",
    }
    return row


def inject_data_quality_issues(rows: list[dict]) -> list[dict]:
    n = len(rows)

    for i in random.sample(range(n), max(1, int(n * 0.015))):
        rows[i]["vendor_name"] = ""

    for i in random.sample(range(n), max(1, int(n * 0.01))):
        rows[i]["total_amount"] = -abs(float(rows[i]["total_amount"]))

    for i in random.sample(range(n), max(1, int(n * 0.01))):
        rows[i]["total_amount"] = round(float(rows[i]["net_amount"]) * 0.5, 2)

    for i in random.sample(range(n), max(1, int(n * 0.005))):
        rows[i]["transaction_date"] = ""

    duplicates = []
    for i in random.sample(range(n), max(1, int(n * 0.03))):
        duplicates.append(dict(rows[i]))
    rows.extend(duplicates)
    random.shuffle(rows)
    return rows


def generate() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    dept_cost_centers = {}
    for entity in BUSINESS_ENTITIES:
        for dept_name, dept_abbr in DEPARTMENTS:
            entity_suffix = entity["country"][:2].upper()
            n_centers = random.choice([1, 1, 2])
            codes = [f"{dept_abbr}-{random.randint(100, 999)}-{entity_suffix}" for _ in range(n_centers)]
            dept_cost_centers[(entity["name"], dept_name)] = codes

    total_rows = 0
    for month_index, (year, month) in enumerate(month_sequence(*START_YEAR_MONTH, NUM_MONTHS)):
        rows = []
        base_volume = 70 + int(month_index * 0.6)
        num_transactions = base_volume + random.randint(-10, 15)

        seq = 1
        for _ in range(num_transactions):
            entity = random.choice(BUSINESS_ENTITIES)
            dept_name, _ = random.choice(DEPARTMENTS)
            cost_center = random.choice(dept_cost_centers[(entity["name"], dept_name)])
            rows.append(build_row(seq, year, month, entity, dept_name, cost_center))
            seq += 1

        for vendor_name in RECURRING_VENDORS:
            for entity in BUSINESS_ENTITIES:
                if random.random() < 0.6:
                    dept_name = random.choice(["R&D", "IT", "Finance", "HR", "Operations", "Sales", "Customer Success"])
                    cost_center = random.choice(dept_cost_centers[(entity["name"], dept_name)])
                    rows.append(build_row(seq, year, month, entity, dept_name, cost_center, vendor_name=vendor_name))
                    seq += 1

        rows = inject_data_quality_issues(rows)
        total_rows += len(rows)

        out_path = OUTPUT_DIR / f"finops_upload_{year}_{month:02d}.csv"
        with out_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    print(f"Generated {total_rows} raw transaction rows across {NUM_MONTHS} monthly files in {OUTPUT_DIR}")


if __name__ == "__main__":
    generate()
