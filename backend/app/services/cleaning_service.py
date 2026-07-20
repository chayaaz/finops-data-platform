from sqlalchemy.orm import Session

from app.models.enums import ApprovalStatus, IngestionStatus
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


def process_batch(db: Session, batch: IngestionBatch) -> None:
    rules = _load_active_rules(db)
    cache = _DimensionCache(db)

    raw_rows = db.query(RawTransaction).filter(RawTransaction.batch_id == batch.id).all()
    existing_record_ids = {
        row[0] for row in db.query(CleanTransaction.record_id).filter(CleanTransaction.batch_id != batch.id).all()
    }

    seen_in_batch: set[str] = set()
    accepted = 0
    rejected = 0

    for raw in raw_rows:
        row_issues: list[DataQualityIssue] = []

        record_id = clean_text(raw.record_id)
        if not record_id:
            rejected += 1
            continue

        if record_id in seen_in_batch or record_id in existing_record_ids:
            _flag(db, rules, "DUPLICATE_RECORD_ID", batch.id, f"Duplicate record_id '{record_id}'", raw.id)
            rejected += 1
            continue
        seen_in_batch.add(record_id)

        transaction_date = parse_date(raw.transaction_date)
        if transaction_date is None:
            _flag(db, rules, "MISSING_DATE", batch.id, f"Unparseable transaction_date for '{record_id}'", raw.id)
            rejected += 1
            continue

        vendor_name = clean_text(raw.vendor_name)
        if not vendor_name:
            row_issues.append(
                _flag(db, rules, "MISSING_VENDOR", batch.id, f"Vendor name missing for '{record_id}'", raw.id)
            )

        net_amount = parse_amount(raw.net_amount) or 0.0
        tax_amount = parse_amount(raw.tax_amount) or 0.0
        total_amount = parse_amount(raw.total_amount)
        if total_amount is None:
            total_amount = net_amount + tax_amount

        if total_amount < net_amount:
            row_issues.append(
                _flag(db, rules, "INVALID_AMOUNT", batch.id, f"total_amount < net_amount for '{record_id}'", raw.id)
            )
        if total_amount < 0:
            row_issues.append(
                _flag(db, rules, "NEGATIVE_AMOUNT", batch.id, f"Negative total_amount for '{record_id}'", raw.id)
            )

        currency = normalize_currency(raw.currency) or "USD"
        business_entity = cache.business_entity(raw.business_entity)
        vendor = cache.vendor(vendor_name)
        if vendor_name and vendor is None:
            row_issues.append(
                _flag(db, rules, "UNKNOWN_VENDOR", batch.id, f"Vendor '{vendor_name}' not in master data", raw.id)
            )

        cost_center = cache.cost_center(raw.cost_center)
        if raw.cost_center and cost_center is None:
            row_issues.append(
                _flag(
                    db, rules, "UNKNOWN_COST_CENTER", batch.id,
                    f"Cost center '{raw.cost_center}' not in master data", raw.id,
                )
            )

        department = cache.department(business_entity.id if business_entity else None, raw.department)
        category = cache.category(raw.category)
        region = cache.region(raw.region)

        approval_status = APPROVAL_STATUS_MAP.get(
            (raw.approval_status or "").strip().lower(), ApprovalStatus.PENDING
        )

        base_amount = fx_service.convert_to_base(db, total_amount, currency, transaction_date)

        clean = CleanTransaction(
            raw_transaction_id=raw.id,
            batch_id=batch.id,
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
        db.add(clean)
        for issue in row_issues:
            if issue is not None:
                issue.clean_transaction = clean
        accepted += 1

    batch.row_count = len(raw_rows)
    batch.accepted_count = accepted
    batch.rejected_count = rejected
    batch.status = IngestionStatus.COMPLETED
