"""
Pydantic schemas for supervisor tools endpoints.
"""

from typing import List, Optional, Literal
from datetime import date
from pydantic import BaseModel, Field


class AssignmentItem(BaseModel):
    """Single employee assignment"""
    employee_id: int
    hours: float = Field(gt=0, description="Actual hours to assign")
    qty: float = Field(gt=0, description="Quantity to assign")


class AssignWorkRequest(BaseModel):
    """Request payload for POST /assign"""
    work_order_id: int
    activity_code_id: int
    assignments: List[AssignmentItem]
    mode: Literal["manual", "auto_split_hours"] = "manual"
    entry_date: date = Field(default_factory=date.today, description="Entry date for jobcards")
    status: Literal["C", "IC"] = "C"


class AssignWorkResponse(BaseModel):
    """Response for POST /assign"""
    created_jobcards: List[int] = Field(description="IDs of created jobcards")
    audit_log_id: int


class ValidationFlagDetail(BaseModel):
    """Validation flag with jobcard details"""
    flag_id: int
    job_card_id: int
    flag_type: str
    details: str
    resolved: bool
    resolved_by: Optional[int] = None
    
    # Jobcard details
    employee_id: Optional[int] = None
    employee_name: Optional[str] = None
    machine_code: Optional[str] = None
    wo_number: Optional[str] = None
    activity_code: Optional[str] = None
    entry_date: Optional[date] = None
    actual_hours: Optional[float] = None
    qty: Optional[float] = None


class ResolveValidationRequest(BaseModel):
    """Request to resolve a validation flag"""
    comment: Optional[str] = Field(None, description="Optional comment about resolution")


class ResolveValidationResponse(BaseModel):
    """Response for PATCH /validations/{flag_id}/resolve"""
    flag_id: int
    resolved: bool
    resolved_by: int
    audit_log_id: int
