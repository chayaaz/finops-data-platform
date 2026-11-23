from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import get_db
from app.deps import require_roles
from app.models.audit import AuditLog
from app.models.enums import UserRole
from app.models.quality import DataQualityRule
from app.models.user import User
from app.schemas.admin import AuditLogRead, DataQualityRuleRead, DataQualityRuleUpdate
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.audit_service import log_action

router = APIRouter(prefix="/admin", tags=["admin"])

_admin_only = require_roles(UserRole.ADMIN)


@router.get("/users", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db), _user: User = Depends(_admin_only)) -> list[UserRead]:
    return db.query(User).order_by(User.full_name).all()


@router.post("/users", response_model=UserRead)
def create_user(payload: UserCreate, db: Session = Depends(get_db), admin: User = Depends(_admin_only)) -> UserRead:
    if db.query(User).filter(User.email == payload.email).first() is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    new_user = User(
        email=payload.email,
        full_name=payload.full_name,
        role=payload.role,
        hashed_password=hash_password(payload.password),
    )
    db.add(new_user)
    log_action(db, admin.id, "user_created", "user")
    db.commit()
    db.refresh(new_user)
    return new_user


@router.patch("/users/{user_id}", response_model=UserRead)
def update_user(
    user_id: int, payload: UserUpdate, db: Session = Depends(get_db), admin: User = Depends(_admin_only)
) -> UserRead:
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if target.role == UserRole.ADMIN and payload.is_active is False:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin accounts cannot be disabled")

    # Prevents an admin from locking themselves out by demoting their own account.
    if target.id == admin.id and payload.role is not None and payload.role != target.role:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot change your own role")

    previous_role = target.role
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(target, field, value)

    details = None
    if payload.role is not None and payload.role != previous_role:
        details = f"role: {previous_role.value} -> {payload.role.value}"
    log_action(db, admin.id, "user_updated", "user", str(user_id), details=details)
    db.commit()
    db.refresh(target)
    return target


@router.get("/rules", response_model=list[DataQualityRuleRead])
def list_rules(db: Session = Depends(get_db), _user: User = Depends(_admin_only)) -> list[DataQualityRuleRead]:
    return db.query(DataQualityRule).order_by(DataQualityRule.code).all()


@router.patch("/rules/{rule_id}", response_model=DataQualityRuleRead)
def update_rule(
    rule_id: int, payload: DataQualityRuleUpdate, db: Session = Depends(get_db), admin: User = Depends(_admin_only)
) -> DataQualityRuleRead:
    rule = db.get(DataQualityRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)

    log_action(db, admin.id, "data_quality_rule_updated", "data_quality_rule", str(rule_id))
    db.commit()
    db.refresh(rule)
    return rule


@router.get("/audit-log", response_model=list[AuditLogRead])
def audit_log(
    db: Session = Depends(get_db),
    _user: User = Depends(_admin_only),
    skip: int = 0,
    limit: int = 200,
) -> list[AuditLogRead]:
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
