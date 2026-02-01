"""
Pydantic schemas for WorkOrder CRUD operations.
"""

from pydantic import BaseModel, Field
from typing import Optional


class WorkOrderBase(BaseModel):
    """Base schema for WorkOrder."""
    wo_number: str = Field(..., min_length=1, max_length=50, description="Work order number")
    machine_id: int = Field(..., gt=0, description="Machine ID")
    planned_qty: float = Field(..., gt=0, description="Planned quantity")
    msd_month: str = Field(..., pattern=r'^\d{4}-\d{2}$', description="MSD month in YYYY-MM format")


class WorkOrderCreate(WorkOrderBase):
    """Schema for creating a WorkOrder."""
    pass


class WorkOrderUpdate(BaseModel):
    """Schema for updating a WorkOrder (all fields optional)."""
    wo_number: Optional[str] = Field(None, min_length=1, max_length=50)
    machine_id: Optional[int] = Field(None, gt=0)
    planned_qty: Optional[float] = Field(None, gt=0)
    msd_month: Optional[str] = Field(None, pattern=r'^\d{4}-\d{2}$')


class WorkOrderRead(WorkOrderBase):
    """Schema for reading a WorkOrder."""
    id: int
    
    class Config:
        from_attributes = True


class WorkOrderWithMachine(WorkOrderRead):
    """Schema for WorkOrder with machine details."""
    machine_code: Optional[str] = None
    machine_description: Optional[str] = None
