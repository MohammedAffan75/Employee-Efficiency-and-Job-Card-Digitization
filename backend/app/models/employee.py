from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import date, datetime
from enum import Enum

from app.models.models import EfficiencyTypeEnum


class RoleEnum(str, Enum):
    OPERATOR = "OPERATOR"
    SUPERVISOR = "SUPERVISOR"
    ADMIN = "ADMIN"


class Employee(SQLModel, table=True):
    """Employee model for efficiency tracking system."""
    
    __tablename__ = "employees"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    ec_number: str = Field(unique=True, index=True)  # Employee Code
    name: str
    role: RoleEnum
    join_date: date
    hashed_password: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    # Track who created this employee (supervisor or admin)
    created_by: Optional[int] = Field(default=None, foreign_key="employees.id")
    # For SUPERVISOR role: which efficiency module they are responsible for
    supervisor_efficiency_module: Optional[EfficiencyTypeEnum] = Field(default=None)
