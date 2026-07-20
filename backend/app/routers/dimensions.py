from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user
from app.models.org import BusinessEntity, CostCenter, Department, Region
from app.models.vendor import Category
from app.schemas.dimension import BusinessEntityRead, CategoryRead, CostCenterRead, DepartmentRead, RegionRead

router = APIRouter(prefix="/dimensions", tags=["dimensions"])


@router.get("/business-entities", response_model=list[BusinessEntityRead])
def business_entities(db: Session = Depends(get_db), _user=Depends(get_current_user)) -> list[BusinessEntityRead]:
    return db.query(BusinessEntity).order_by(BusinessEntity.name).all()


@router.get("/departments", response_model=list[DepartmentRead])
def departments(db: Session = Depends(get_db), _user=Depends(get_current_user)) -> list[DepartmentRead]:
    return db.query(Department).order_by(Department.name).all()


@router.get("/cost-centers", response_model=list[CostCenterRead])
def cost_centers(db: Session = Depends(get_db), _user=Depends(get_current_user)) -> list[CostCenterRead]:
    return db.query(CostCenter).order_by(CostCenter.code).all()


@router.get("/regions", response_model=list[RegionRead])
def regions(db: Session = Depends(get_db), _user=Depends(get_current_user)) -> list[RegionRead]:
    return db.query(Region).order_by(Region.name).all()


@router.get("/categories", response_model=list[CategoryRead])
def categories(db: Session = Depends(get_db), _user=Depends(get_current_user)) -> list[CategoryRead]:
    return db.query(Category).order_by(Category.name).all()
