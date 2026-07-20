from collections import defaultdict

import numpy as np
from sqlalchemy.orm import Session

from app.models.ingestion import CleanTransaction
from app.models.quality import Anomaly

MIN_SAMPLE_SIZE = 5
DEFAULT_Z_THRESHOLD = 3.0

BENFORD_EXPECTED = {d: np.log10(1 + 1 / d) for d in range(1, 10)}


def detect_zscore_anomalies(db: Session, z_threshold: float = DEFAULT_Z_THRESHOLD) -> int:
    """Flags transactions whose amount is a statistical outlier within its own vendor's
    spend history (rolling mean/std), i.e. this vendor suddenly billed far more than usual."""
    rows = (
        db.query(CleanTransaction.id, CleanTransaction.vendor_id, CleanTransaction.total_amount_base_currency)
        .filter(CleanTransaction.vendor_id.isnot(None), CleanTransaction.total_amount_base_currency.isnot(None))
        .all()
    )

    by_vendor: dict[int, list[tuple[int, float]]] = defaultdict(list)
    for tx_id, vendor_id, amount in rows:
        by_vendor[vendor_id].append((tx_id, float(amount)))

    already_flagged = {
        (a.clean_transaction_id, a.anomaly_type)
        for a in db.query(Anomaly.clean_transaction_id, Anomaly.anomaly_type).filter(Anomaly.anomaly_type == "AMOUNT_ZSCORE")
    }

    created = 0
    for vendor_id, entries in by_vendor.items():
        if len(entries) < MIN_SAMPLE_SIZE:
            continue
        amounts = np.array([amount for _, amount in entries])
        mean, std = amounts.mean(), amounts.std()
        if std == 0:
            continue

        for tx_id, amount in entries:
            z = (amount - mean) / std
            if abs(z) >= z_threshold and (tx_id, "AMOUNT_ZSCORE") not in already_flagged:
                db.add(
                    Anomaly(
                        clean_transaction_id=tx_id,
                        anomaly_type="AMOUNT_ZSCORE",
                        z_score=round(float(z), 4),
                        detail=f"Amount deviates {z:.1f} standard deviations from this vendor's typical spend",
                    )
                )
                created += 1

    return created


def leading_digit(amount: float) -> int | None:
    text = f"{abs(amount):.10f}".lstrip("0.").lstrip("0")
    for ch in text:
        if ch.isdigit() and ch != "0":
            return int(ch)
    return None


def benford_distribution(db: Session, group_by: str = "category") -> list[dict]:
    """Compares the leading-digit distribution of transaction amounts against Benford's
    Law; a real, fraud-detection-relevant statistical test that Excel cannot do natively."""
    query = db.query(
        CleanTransaction.category_id if group_by == "category" else CleanTransaction.vendor_id,
        CleanTransaction.total_amount_base_currency,
    ).filter(CleanTransaction.total_amount_base_currency.isnot(None), CleanTransaction.total_amount_base_currency > 0)

    grouped: dict[int, list[float]] = defaultdict(list)
    for group_id, amount in query.all():
        if group_id is not None:
            grouped[group_id].append(float(amount))

    results = []
    for group_id, amounts in grouped.items():
        if len(amounts) < 30:
            continue
        digit_counts = defaultdict(int)
        for amount in amounts:
            digit = leading_digit(amount)
            if digit:
                digit_counts[digit] += 1

        total = sum(digit_counts.values())
        observed = {d: digit_counts.get(d, 0) / total for d in range(1, 10)}
        chi_square = sum(
            ((observed[d] - BENFORD_EXPECTED[d]) ** 2) / BENFORD_EXPECTED[d] for d in range(1, 10)
        ) * total

        results.append(
            {
                "group_id": group_id,
                "sample_size": total,
                "chi_square": round(chi_square, 2),
                "observed_distribution": {d: round(observed[d], 4) for d in range(1, 10)},
                "expected_distribution": {d: round(BENFORD_EXPECTED[d], 4) for d in range(1, 10)},
                "flagged": chi_square > 15.51,  # chi-square critical value, df=8, alpha=0.05
            }
        )

    return sorted(results, key=lambda r: r["chi_square"], reverse=True)
