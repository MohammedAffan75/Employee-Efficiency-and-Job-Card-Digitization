"""
Pydantic schemas for Machine CRUD operations.
"""

from pydantic import BaseModel, Field
from typing import Optional


class MachineBase(BaseModel):
    """Base schema for Machine."""
    machine_code: str = Field(..., min_length=1, max_length=50, description="Unique machine code")
    description: str = Field(..., min_length=1, max_length=200, description="Machine description")
    work_center: str = Field(..., min_length=1, max_length=100, description="Work center")


class MachineCreate(MachineBase):
    """Schema for creating a Machine."""
    pass


class MachineUpdate(BaseModel):
    """Schema for updating a Machine (all fields optional)."""
    machine_code: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, min_length=1, max_length=200)
    work_center: Optional[str] = Field(None, min_length=1, max_length=100)


class MachineRead(MachineBase):
    """Schema for reading a Machine."""
    id: int
    
    class Config:
        from_attributes = True
