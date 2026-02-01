from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional
from app.models.employee import RoleEnum
from app.models.models import EfficiencyTypeEnum


class EmployeeBase(BaseModel):
    """Base employee schema."""
    ec_number: str
    name: str
    role: RoleEnum
    team: Optional[str] = None
    join_date: date
    supervisor_efficiency_module: Optional[EfficiencyTypeEnum] = None


class EmployeeCreate(EmployeeBase):
    """Schema for creating an employee."""
    password: str


class EmployeeRead(EmployeeBase):
    """Schema for reading employee data."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmployeeUpdate(BaseModel):
    """Schema for updating employee data."""
    name: Optional[str] = None
    role: Optional[RoleEnum] = None
    team: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None  # Allow password update
