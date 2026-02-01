"""
Pydantic schemas for JobCard CRUD operations.
"""

from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class JobCardBase(BaseModel):
    """Base schema for JobCard."""
    employee_id: Optional[int] = Field(None, description="Employee ID (optional)")
    supervisor_id: Optional[int] = Field(None, description="Supervisor ID (optional)")
    machine_id: Optional[int] = Field(None, gt=0, description="Machine ID (optional for task-based)")
    work_order_id: Optional[int] = Field(None, gt=0, description="Work order ID (optional for task-based)")
    activity_code_id: Optional[int] = Field(None, description="Activity code ID (optional)")
    activity_desc: str = Field(..., min_length=1, max_length=200, description="Activity description")
    qty: float = Field(..., ge=0, description="Quantity completed")
    actual_hours: float = Field(..., gt=0, description="Actual hours worked")
    manual_machine_text: Optional[str] = Field(
        None,
        description="Optional free-text machine description for task-based/AWC entries",
    )
    manual_work_order_text: Optional[str] = Field(
        None,
        description="Optional free-text work order identifier for task-based/AWC entries",
    )
    shift: Optional[int] = Field(None, description="Shift: 1, 2, or 3")
    is_awc: bool = Field(default=False, description="Activity Without Code")
    status: str = Field(default="IC", description="Status: IC (Incomplete) or C (Complete)")
    entry_date: date = Field(..., description="Entry date")
    source: str = Field(..., description="Source: TECHNICIAN or SUPERVISOR")
    approval_status: str = Field(default="PENDING", description="Approval status: PENDING, APPROVED, REJECTED")
    supervisor_remarks: Optional[str] = Field(None, description="Supervisor remarks for approval/rejection")
    approved_at: Optional[datetime] = Field(None, description="Approval/rejection timestamp")
    approved_by: Optional[int] = Field(None, description="Supervisor who approved/rejected")
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v not in ['IC', 'C']:
            raise ValueError('Status must be either IC or C')
        return v
    
    @field_validator('source')
    @classmethod
    def validate_source(cls, v):
        if v not in ['TECHNICIAN', 'SUPERVISOR']:
            raise ValueError('Source must be either TECHNICIAN or SUPERVISOR')
        return v
    
    @field_validator('approval_status')
    @classmethod
    def validate_approval_status(cls, v):
        if v not in ['PENDING', 'APPROVED', 'REJECTED']:
            raise ValueError('Approval status must be PENDING, APPROVED, or REJECTED')
        return v


class JobCardCreate(JobCardBase):
    """Schema for creating a JobCard."""
    pass


class JobCardUpdate(BaseModel):
    """Schema for updating a JobCard (all fields optional)."""
    employee_id: Optional[int] = None
    supervisor_id: Optional[int] = None
    machine_id: Optional[int] = Field(None, gt=0)
    work_order_id: Optional[int] = Field(None, gt=0)
    activity_code_id: Optional[int] = None
    activity_desc: Optional[str] = Field(None, min_length=1, max_length=200)
    qty: Optional[float] = Field(None, ge=0)
    actual_hours: Optional[float] = Field(None, gt=0)
    shift: Optional[int] = Field(None)
    is_awc: Optional[bool] = Field(None)
    status: Optional[str] = None
    entry_date: Optional[date] = None
    source: Optional[str] = None
    approval_status: Optional[str] = None
    supervisor_remarks: Optional[str] = Field(None, max_length=500)
    approved_at: Optional[datetime] = None
    approved_by: Optional[int] = None
    manual_machine_text: Optional[str] = Field(
        None,
        description="Optional free-text machine description for task-based/AWC entries",
    )
    manual_work_order_text: Optional[str] = Field(
        None,
        description="Optional free-text work order identifier for task-based/AWC entries",
    )
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v is not None and v not in ['IC', 'C']:
            raise ValueError('Status must be either IC or C')
        return v
    
    @field_validator('source')
    @classmethod
    def validate_source(cls, v):
        if v is not None and v not in ['TECHNICIAN', 'SUPERVISOR']:
            raise ValueError('Source must be either TECHNICIAN or SUPERVISOR')
        return v
    
    @field_validator('approval_status')
    @classmethod
    def validate_approval_status(cls, v):
        if v is not None and v not in ['PENDING', 'APPROVED', 'REJECTED']:
            raise ValueError('Approval status must be PENDING, APPROVED, or REJECTED')
        return v


class JobCardRead(JobCardBase):
    """Schema for reading a JobCard."""
    id: int
    
    class Config:
        from_attributes = True


class JobCardWithDetails(JobCardRead):
    """Schema for JobCard with related details."""
    employee_name: Optional[str] = None
    supervisor_name: Optional[str] = None
    machine_code: Optional[str] = None
    wo_number: Optional[str] = None
    activity_code: Optional[str] = None
    efficiency_module: Optional[str] = None
    has_flags: bool = False
    approval_status: Optional[str] = None
    supervisor_remarks: Optional[str] = None
    approved_at: Optional[str] = None
    approved_by_name: Optional[str] = None
    std_hours_per_unit: Optional[float] = None
    std_qty_per_hour: Optional[float] = None


class SupervisorApprovalRequest(BaseModel):
    """Schema for supervisor approval/rejection actions."""
    action: str = Field(..., description="Action: APPROVE or REJECT")
    remarks: Optional[str] = Field(None, max_length=500, description="Supervisor feedback")
    
    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        if v not in ['APPROVE', 'REJECT']:
            raise ValueError('Action must be APPROVE or REJECT')
        return v


class SupervisorApprovalResponse(BaseModel):
    """Schema for supervisor approval response."""
    job_card_id: int
    approval_status: str
    approved_by: int
    approved_at: str
    remarks: Optional[str] = None


class JobCardReview(BaseModel):
    """Schema for job cards pending supervisor review."""
    id: int
    employee_id: Optional[int] = None
    employee_name: Optional[str] = None
    employee_ec_number: Optional[str] = None
    machine_code: Optional[str] = None
    wo_number: Optional[str] = None
    activity_desc: str
    activity_code: Optional[str] = None
    efficiency_module: str  # TIME_BASED, QUANTITY_BASED, TASK_BASED
    qty: float
    actual_hours: float
    status: str
    entry_date: str
    shift: int = Field(None, description="Shift: 1, 2, or 3")
    approval_status: str
    has_flags: bool = False
    std_hours_per_unit: Optional[float] = None
    std_qty_per_hour: Optional[float] = None
