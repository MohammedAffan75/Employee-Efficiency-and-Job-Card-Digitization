"""
Pydantic schemas for bulk import functionality.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class RejectedRow(BaseModel):
    """Details of a rejected import row"""
    row_number: int
    data: dict
    reason: str


class FlaggedJobCard(BaseModel):
    """JobCard that was imported but has validation flags"""
    jobcard_id: int
    flags: List[str] = Field(description="List of flag types")


class ImportReport(BaseModel):
    """Report of import operation"""
    total_rows: int
    accepted_count: int
    rejected_count: int
    flagged_count: int
    rejected: List[RejectedRow] = []
    flagged: List[FlaggedJobCard] = []
    
    
class ImportJobCardRow(BaseModel):
    """Single row from import file"""
    ec_number: str = Field(description="Employee EC number")
    entry_date: str = Field(description="Entry date (YYYY-MM-DD)")
    shift: Optional[str] = None
    machine_code: str
    wo_number: str = Field(description="Work order number")
    activity_code: Optional[str] = None
    activity_desc: str
    qty: float
    actual_hours: float
    status: str = Field(description="C or IC")
