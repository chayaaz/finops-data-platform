from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class BusinessEntity(Base):
    __tablename__ = "business_entities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    legal_name: Mapped[str] = mapped_column(String(255))
    country: Mapped[str] = mapped_column(String(100))
    base_currency: Mapped[str] = mapped_column(String(3))

    departments: Mapped[list["Department"]] = relationship(back_populates="business_entity")


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    business_entity_id: Mapped[int] = mapped_column(ForeignKey("business_entities.id"))

    business_entity: Mapped[BusinessEntity] = relationship(back_populates="departments")
    cost_centers: Mapped[list["CostCenter"]] = relationship(back_populates="department")


class CostCenter(Base):
    __tablename__ = "cost_centers"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))

    department: Mapped[Department] = relationship(back_populates="cost_centers")


class Region(Base):
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(255))
