from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user, require_roles
from app.models.budget import Budget
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.budget import BudgetCreate, BudgetRead, BudgetUpdate, BudgetVarianceRow, BurnDownPoint
from app.services import budget_service
from app.services.audit_service import log_action

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.get("", response_model=list[BudgetRead])
def list_budgets(
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
    cost_center_id: int | None = None,
    category_id: int | None = None,
) -> list[BudgetRead]:
    query = db.query(Budget)
    if cost_center_id is not None:
        query = query.filter(Budget.cost_center_id == cost_center_id)
    if category_id is not None:
        query = query.filter(Budget.category_id == category_id)
    return query.order_by(Budget.period_month.desc()).all()


@router.get("/variance", response_model=list[BudgetVarianceRow])
def variance(
    period_start: date,
    period_end: date,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
    cost_center_id: int | None = None,
    category_id: int | None = None,
) -> list[BudgetVarianceRow]:
    return budget_service.budget_vs_actual(db, period_start, period_end, cost_center_id, category_id)


@router.get("/burn-down", response_model=list[BurnDownPoint])
def burn_down(
    year: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
    cost_center_id: int | None = None,
    category_id: int | None = None,
) -> list[BurnDownPoint]:
    return budget_service.burn_down(db, year, cost_center_id, category_id)


@router.post("", response_model=BudgetRead)
def create_budget(
    payload: BudgetCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.FINANCE_MANAGER)),
) -> BudgetRead:
    budget = Budget(**payload.model_dump())
    db.add(budget)
    log_action(db, user.id, "budget_created", "budget")
    db.commit()
    db.refresh(budget)
    return budget


@router.patch("/{budget_id}", response_model=BudgetRead)
def update_budget(
    budget_id: int,
    payload: BudgetUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.FINANCE_MANAGER)),
) -> BudgetRead:
    budget = db.get(Budget, budget_id)
    if budget is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")

    budget.budget_amount = payload.budget_amount
    log_action(db, user.id, "budget_updated", "budget", str(budget_id))
    db.commit()
    db.refresh(budget)
    return budget
