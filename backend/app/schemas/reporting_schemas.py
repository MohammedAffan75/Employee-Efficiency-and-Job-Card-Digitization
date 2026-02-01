"""
Pydantic schemas for reporting endpoints.
"""

from typing import Optional
from pydantic import BaseModel, Field


class DashboardSummary(BaseModel):
    """Team dashboard KPIs summary"""
    team_id: Optional[str] = None
    period_start: str
    period_end: str
    employee_count: int = Field(description="Number of employees in report")
    avg_time_efficiency: float = Field(description="Average time efficiency %")
    avg_qty_efficiency: float = Field(description="Average quantity efficiency %")
    avg_task_efficiency: float = Field(description="Average task efficiency %")
    avg_awc_pct: float = Field(description="Average AWC percentage")
    total_std_hours: float = Field(description="Total standard hours allowed")
    total_actual_hours: float = Field(description="Total actual hours")
