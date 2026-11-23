from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.enums import ApprovalStatus, IngestionStatus, IssueStatus
from app.models.ingestion import CleanTransaction, IngestionBatch, RawTransaction
from app.models.org import BusinessEntity, CostCenter, Department, Region
from app.models.quality import DataQualityIssue, DataQualityRule
from app.models.vendor import Category, Vendor
from app.services import fx_service
from app.services.normalization import clean_text, normalize_currency, normalize_payment_method, parse_amount, parse_date

APPROVAL_STATUS_MAP = {status.value.lower(): status for status in ApprovalStatus}


class _DimensionCache:
    def __init__(self, db: Session):
        self.vendors = {v.name.strip().lower(): v for v in db.query(Vendor).all()}
        self.categories = {c.name.strip().lower(): c for c in db.query(Category).all()}
        self.business_entities = {e.name.strip().lower(): e for e in db.query(BusinessEntity).all()}
        self.regions = {r.code.strip().lower(): r for r in db.query(Region).all()}
        self.cost_centers = {cc.code.strip().lower(): cc for cc in db.query(CostCenter).all()}
        self.departments = {
            (d.business_entity_id, d.name.strip().lower()): d for d in db.query(Department).all()
        }

    def vendor(self, name: str | None) -> Vendor | None:
        return self.vendors.get(name.strip().lower()) if name else None

    def category(self, name: str | None) -> Category | None:
        return self.categories.get(name.strip().lower()) if name else None

    def business_entity(self, name: str | None) -> BusinessEntity | None:
        return self.business_entities.get(name.strip().lower()) if name else None

    def region(self, code: str | None) -> Region | None:
        return self.regions.get(code.strip().lower()) if code else None

    def cost_center(self, code: str | None) -> CostCenter | None:
        return self.cost_centers.get(code.strip().lower()) if code else None

    def department(self, business_entity_id: int | None, name: str | None) -> Department | None:
        if not business_entity_id or not name:
            return None
        return self.departments.get((business_entity_id, name.strip().lower()))


def _load_active_rules(db: Session) -> dict[str, DataQualityRule]:
    rules = db.query(DataQualityRule).filter(DataQualityRule.is_active.is_(True)).all()
    return {rule.code: rule for rule in rules}


def _flag(
    db: Session,
    rules: dict[str, DataQualityRule],
    code: str,
    batch_id: int,
    description: str,
    raw_transaction_id: int | None = None,
) -> DataQualityIssue | None:
    rule = rules.get(code)
    if rule is None:
        return None
    issue = DataQualityIssue(
        batch_id=batch_id,
        raw_transaction_id=raw_transaction_id,
        rule_code=code,
        severity=rule.severity,
        description=description,
    )
    db.add(issue)
    return issue


@dataclass
class RowResult:
    """Outcome of validating one raw row. `clean` is None when the row is rejected;
    `problems` lists (rule_code, description) pairs, blocking or not."""

    clean: CleanTransaction | None
    problems: list[tuple[str, str]] = field(default_factory=list)


def _evaluate_row(db: Session, cache: _DimensionCache, raw: RawTransaction, taken_record_ids: set[str]) -> RowResult:
    """Applies every cleaning rule to a single raw row. Adds the row's record_id to
    `taken_record_ids` once it passes the duplicate check, so later rows in the same
    batch are compared against it."""
    record_id = clean_text(raw.record_id)
    if not record_id:
        return RowResult(clean=None)

    if record_id in taken_record_ids:
        return RowResult(clean=None, problems=[("DUPLICATE_RECORD_ID", f"Duplicate record_id '{record_id}'")])
    taken_record_ids.add(record_id)

    transaction_date = parse_date(raw.transaction_date)
    if transaction_date is None:
        return RowResult(clean=None, problems=[("MISSING_DATE", f"Unparseable transaction_date for '{record_id}'")])

    problems: list[tuple[str, str]] = []

    vendor_name = clean_text(raw.vendor_name)
    if not vendor_name:
        problems.append(("MISSING_VENDOR", f"Vendor name missing for '{record_id}'"))

    net_amount = parse_amount(raw.net_amount) or 0.0
    tax_amount = parse_amount(raw.tax_amount) or 0.0
    total_amount = parse_amount(raw.total_amount)
    if total_amount is None:
        total_amount = net_amount + tax_amount

    if total_amount < net_amount:
        problems.append(("INVALID_AMOUNT", f"total_amount < net_amount for '{record_id}'"))
    if total_amount < 0:
        problems.append(("NEGATIVE_AMOUNT", f"Negative total_amount for '{record_id}'"))

    currency = normalize_currency(raw.currency) or "USD"
    business_entity = cache.business_entity(raw.business_entity)
    vendor = cache.vendor(vendor_name)
    if vendor_name and vendor is None:
        problems.append(("UNKNOWN_VENDOR", f"Vendor '{vendor_name}' not in master data"))

    cost_center = cache.cost_center(raw.cost_center)
    if raw.cost_center and cost_center is None:
        problems.append(("UNKNOWN_COST_CENTER", f"Cost center '{raw.cost_center}' not in master data"))

    department = cache.department(business_entity.id if business_entity else None, raw.department)
    category = cache.category(raw.category)
    region = cache.region(raw.region)

    approval_status = APPROVAL_STATUS_MAP.get(
        (raw.approval_status or "").strip().lower(), ApprovalStatus.PENDING
    )

    base_amount = fx_service.convert_to_base(db, total_amount, currency, transaction_date)

    clean = CleanTransaction(
        raw_transaction_id=raw.id,
        batch_id=raw.batch_id,
        record_id=record_id,
        vendor_id=vendor.id if vendor else None,
        department_id=department.id if department else None,
        cost_center_id=cost_center.id if cost_center else None,
        category_id=category.id if category else None,
        business_entity_id=business_entity.id if business_entity else None,
        region_id=region.id if region else None,
        invoice_number=clean_text(raw.invoice_number),
        transaction_date=transaction_date,
        posting_date=parse_date(raw.posting_date),
        item_type=clean_text(raw.item_type),
        description=clean_text(raw.description),
        quantity=parse_amount(raw.quantity),
        unit_of_measure=clean_text(raw.unit_of_measure),
        currency=currency,
        net_amount=net_amount,
        tax_amount=tax_amount,
        total_amount=total_amount,
        total_amount_base_currency=base_amount,
        payment_method=normalize_payment_method(raw.payment_method),
        approval_status=approval_status,
        created_by=clean_text(raw.created_by),
        notes=clean_text(raw.notes),
    )
    return RowResult(clean=clean, problems=problems)


def process_batch(db: Session, batch: IngestionBatch) -> None:
    rules = _load_active_rules(db)
    cache = _DimensionCache(db)

    raw_rows = db.query(RawTransaction).filter(RawTransaction.batch_id == batch.id).all()
    taken_record_ids = {
        row[0] for row in db.query(CleanTransaction.record_id).filter(CleanTransaction.batch_id != batch.id).all()
    }

    accepted = 0
    rejected = 0

    for raw in raw_rows:
        result = _evaluate_row(db, cache, raw, taken_record_ids)
        issues = [_flag(db, rules, code, batch.id, description, raw.id) for code, description in result.problems]

        if result.clean is None:
            rejected += 1
            continue

        db.add(result.clean)
        for issue in issues:
            if issue is not None:
                issue.clean_transaction = result.clean
        accepted += 1

    batch.row_count = len(raw_rows)
    batch.accepted_count = accepted
    batch.rejected_count = rejected
    batch.status = IngestionStatus.COMPLETED


# Raw columns a user may correct when fixing a row from the Data Quality screen.
EDITABLE_RAW_FIELDS = (
    "record_id",
    "transaction_date",
    "vendor_name",
    "department",
    "cost_center",
    "category",
    "currency",
    "net_amount",
    "tax_amount",
    "total_amount",
    "business_entity",
)


class RowStillInvalidError(ValueError):
    pass


def fix_raw_row(db: Session, raw: RawTransaction, corrections: dict[str, str | None], user_id: int) -> RowResult:
    """Applies a user's corrections to a raw row and re-runs the cleaning rules on it.
    A previously rejected row is added to clean_transactions; an accepted row has its
    clean record updated. The row's open issues are resolved and any remaining
    non-blocking problems are flagged afresh. Raises RowStillInvalidError, without
    writing anything, when the corrected row would still be rejected."""
    for field_name, value in corrections.items():
        if field_name in EDITABLE_RAW_FIELDS:
            setattr(raw, field_name, value)

    existing = db.query(CleanTransaction).filter(CleanTransaction.raw_transaction_id == raw.id).first()
    taken_query = db.query(CleanTransaction.record_id)
    if existing is not None:
        taken_query = taken_query.filter(CleanTransaction.id != existing.id)
    taken_record_ids = {row[0] for row in taken_query.all()}

    result = _evaluate_row(db, _DimensionCache(db), raw, taken_record_ids)
    if result.clean is None:
        reason = "; ".join(description for _, description in result.problems) or "record_id is required"
        raise RowStillInvalidError(reason)

    batch = db.get(IngestionBatch, raw.batch_id)
    if existing is not None:
        for column in CleanTransaction.__table__.columns:
            if column.key != "id":
                setattr(existing, column.key, getattr(result.clean, column.key))
        clean = existing
    else:
        clean = result.clean
        db.add(clean)
        batch.accepted_count += 1
        batch.rejected_count = max(batch.rejected_count - 1, 0)

    now = datetime.now(timezone.utc)
    open_issues = (
        db.query(DataQualityIssue)
        .filter(DataQualityIssue.raw_transaction_id == raw.id, DataQualityIssue.status != IssueStatus.RESOLVED)
        .all()
    )
    for issue in open_issues:
        issue.status = IssueStatus.RESOLVED
        issue.resolved_by_id = user_id
        issue.resolved_at = now

    rules = _load_active_rules(db)
    for code, description in result.problems:
        issue = _flag(db, rules, code, raw.batch_id, description, raw.id)
        if issue is not None:
            issue.clean_transaction = clean

    result.clean = clean
    return result
