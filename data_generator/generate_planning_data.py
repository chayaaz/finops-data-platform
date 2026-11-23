"""Generates budgets, historical FX rates, vendor commitments and seed users."""

import csv
import glob
import random
from collections import defaultdict
from pathlib import Path

from reference_data import BUSINESS_ENTITIES, CURRENCIES, SEED_USERS
from generate_transactions import month_sequence, START_YEAR_MONTH, NUM_MONTHS

random.seed(43)

OUTPUT_DIR = Path(__file__).parent / "output"
RAW_DIR = OUTPUT_DIR / "raw"

# Approximate historical monthly average rates (units of currency per 1 USD), used as a
# realistic anchor for a random-walk series rather than a live FX feed.
FX_ANCHOR_TO_USD = {"USD": 1.0, "EUR": 0.92, "ILS": 3.65}


def generate_exchange_rates() -> None:
    rows = []
    rate = dict(FX_ANCHOR_TO_USD)
    for year, month in month_sequence(*START_YEAR_MONTH, NUM_MONTHS):
        for day in (1, 15):
            for currency in CURRENCIES:
                if currency == "USD":
                    rate_to_base = 1.0
                else:
                    drift = random.uniform(-0.015, 0.015)
                    rate[currency] = max(0.01, rate[currency] * (1 + drift))
                    # rate_to_base expresses 1 unit of `currency` in USD (the base currency)
                    rate_to_base = round(1 / rate[currency], 6)
                rows.append({"rate_date": f"{year}-{month:02d}-{day:02d}", "currency_code": currency, "rate_to_base": rate_to_base})

    out_path = OUTPUT_DIR / "exchange_rates.csv"
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["rate_date", "currency_code", "rate_to_base"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Generated {len(rows)} exchange rate points -> {out_path}")


def _load_raw_transactions() -> list[dict]:
    rows = []
    for path in sorted(glob.glob(str(RAW_DIR / "*.csv"))):
        with open(path, newline="", encoding="utf-8") as f:
            rows.extend(csv.DictReader(f))
    return rows


# Budgets are tightened year over year, so the company-wide view moves from comfortable
# (2023) to close to the limit (2025) and every overall status can be demonstrated.
BUDGET_TIGHTENING_BY_YEAR = {"2023": 1.0, "2024": 0.88, "2025": 0.8}


def generate_budgets() -> None:
    """Set each cost-center/category/month budget relative to its actual spend, in the
    owning entity's base currency, so Budget-vs-Actual shows every status: most categories
    have comfortable headroom, some run close to the limit, and some overspend."""
    rows = _load_raw_transactions()
    currency_by_entity = {e["name"]: e["base_currency"] for e in BUSINESS_ENTITIES}

    spend = defaultdict(float)
    currency_by_cc = {}
    for row in rows:
        try:
            amount = float(row["total_amount"])
        except (TypeError, ValueError):
            continue
        key = (row["cost_center"], row["category"], row["transaction_date"][:7])
        spend[key] += amount
        currency_by_cc[row["cost_center"]] = currency_by_entity.get(row["business_entity"], "USD")

    # Each category gets one budgeting profile per year, so whole categories show up as
    # healthy, tight or overspending rather than the differences averaging out. The value
    # is budget as a multiple of actual spend: 1.4x is ~71% used, 1.12x ~89%, 0.92x ~109%.
    profile_by_category_year: dict[tuple[str, str], float] = {}

    budget_rows = []
    for (cost_center, category, period), actual in sorted(spend.items()):
        # Lines whose only rows are refunds or data errors have no real spend to budget for.
        if not period or len(period) != 7 or actual <= 0:
            continue
        profile_key = (category, period[:4])
        if profile_key not in profile_by_category_year:
            profile_by_category_year[profile_key] = random.choices([1.4, 1.12, 0.92], weights=[55, 28, 17])[0]
        variance_factor = (
            profile_by_category_year[profile_key]
            * BUDGET_TIGHTENING_BY_YEAR.get(period[:4], 1.0)
            * random.uniform(0.9, 1.1)
        )
        budget_amount = round(actual * variance_factor, 2)
        budget_rows.append({
            "cost_center_code": cost_center,
            "category_name": category,
            "period_month": f"{period}-01",
            "currency": currency_by_cc.get(cost_center, "USD"),
            "budget_amount": budget_amount,
        })

    out_path = OUTPUT_DIR / "budgets.csv"
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["cost_center_code", "category_name", "period_month", "currency", "budget_amount"])
        writer.writeheader()
        writer.writerows(budget_rows)
    print(f"Generated {len(budget_rows)} budget rows -> {out_path}")


def generate_commitments() -> None:
    """Reserved-capacity commitments for the major cloud vendors, with utilization that
    sometimes falls short of (wasted spend) or exceeds (overage risk) the commitment."""
    cloud_vendors = ["Google Cloud", "Microsoft Azure", "Amazon Web Services"]
    rows = []
    for year, month in month_sequence(*START_YEAR_MONTH, NUM_MONTHS):
        for entity in BUSINESS_ENTITIES:
            for vendor in cloud_vendors:
                if random.random() < 0.85:
                    committed = round(random.uniform(2000, 12000), 2)
                    utilization_ratio = random.choices(
                        [random.uniform(0.55, 0.8), random.uniform(0.85, 1.05), random.uniform(1.05, 1.3)],
                        weights=[25, 50, 25],
                    )[0]
                    rows.append({
                        "vendor_name": vendor,
                        "business_entity_name": entity["name"],
                        "period_month": f"{year}-{month:02d}-01",
                        "currency": "USD",
                        "committed_amount": committed,
                        "utilized_amount": round(committed * utilization_ratio, 2),
                    })

    out_path = OUTPUT_DIR / "commitments.csv"
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["vendor_name", "business_entity_name", "period_month", "currency", "committed_amount", "utilized_amount"]
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"Generated {len(rows)} commitment rows -> {out_path}")


def generate_users() -> None:
    out_path = OUTPUT_DIR / "users.csv"
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["email", "full_name", "role", "password"])
        writer.writeheader()
        writer.writerows(SEED_USERS)
    print(f"Generated {len(SEED_USERS)} seed users -> {out_path}")


if __name__ == "__main__":
    generate_exchange_rates()
    generate_budgets()
    generate_commitments()
    generate_users()
