"""
Pydantic schemas for ActivityCode CRUD operations.
"""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class ActivityCodeBase(BaseModel):
    """Base schema for ActivityCode."""
    code: str = Field(..., min_length=1, max_length=50, description="Activity code")
    description: str = Field(..., min_length=1, max_length=200, description="Activity description")
    std_hours_per_unit: Optional[float] = Field(None, ge=0, description="Standard hours per unit")
    std_qty_per_hour: Optional[float] = Field(None, ge=0, description="Standard quantity per hour")
    efficiency_type: str = Field(..., description="Efficiency type: TIME_BASED, QUANTITY_BASED, or TASK_BASED")


class ActivityCodeCreate(ActivityCodeBase):
    """Schema for creating an ActivityCode."""
    pass


class ActivityCodeUpdate(BaseModel):
    """Schema for updating an ActivityCode (all fields optional)."""
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, min_length=1, max_length=200)
    std_hours_per_unit: Optional[float] = Field(None, ge=0)
    std_qty_per_hour: Optional[float] = Field(None, ge=0)
    efficiency_type: Optional[str] = None


class ActivityCodeRead(ActivityCodeBase):
    """Schema for reading an ActivityCode."""
    id: int
    last_updated: datetime
    
    class Config:
        from_attributes = True
