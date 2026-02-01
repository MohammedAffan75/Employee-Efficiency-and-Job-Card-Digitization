"""
Employee Efficiency Tracking System - SQLModel Database Models
"""

from typing import Optional
from datetime import date, datetime
from enum import Enum
from sqlmodel import Field, SQLModel, Index


# ==================== ENUMS ====================

class RoleEnum(str, Enum):
    """Employee roles"""
    OPERATOR = "OPERATOR"
    SUPERVISOR = "SUPERVISOR"
    ADMIN = "ADMIN"


class EfficiencyTypeEnum(str, Enum):
    """Activity efficiency calculation methods"""
    TIME_BASED = "TIME_BASED"
    QUANTITY_BASED = "QUANTITY_BASED"
    TASK_BASED = "TASK_BASED"


class JobCardStatusEnum(str, Enum):
    """Job card status"""
    IC = "IC"  # Incomplete
    C = "C"    # Complete


class ApprovalStatusEnum(str, Enum):
    """Supervisor approval status for job cards"""
    PENDING = "PENDING"     # Awaiting supervisor review
    APPROVED = "APPROVED"   # Approved by supervisor
    REJECTED = "REJECTED"   # Rejected by supervisor


class SourceEnum(str, Enum):
    """Data entry source"""
    TECHNICIAN = "TECHNICIAN"
    SUPERVISOR = "SUPERVISOR"


class FlagTypeEnum(str, Enum):
    """Validation flag types"""
    DUPLICATION = "DUPLICATION"
    OUTSIDE_MSD = "OUTSIDE_MSD"
    AWC = "AWC"
    SPLIT_CANDIDATE = "SPLIT_CANDIDATE"
    QTY_MISMATCH = "QTY_MISMATCH"


# ==================== MODELS ====================

class EfficiencyEmployee(SQLModel, table=True):
    """Employee master for efficiency tracking"""
    
    __tablename__ = "efficiency_employees"
    __table_args__ = (
        Index("ix_eff_emp_ec_number", "ec_number"),
    )
    
    id: Optional[int] = Field(default=None, primary_key=True)
    ec_number: str = Field(unique=True, index=True)
    name: str
    hashed_password: str  # Password hash for authentication
    role: RoleEnum
    team: Optional[str] = None
    join_date: date
    is_active: bool = Field(default=True)
    
    def __repr__(self) -> str:
        return f"EfficiencyEmployee(ec={self.ec_number}, name={self.name})"
    
    def __str__(self) -> str:
        return f"{self.ec_number} - {self.name}"


class Machine(SQLModel, table=True):
    """Machine/equipment master"""
    
    __tablename__ = "machines"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    machine_code: str = Field(unique=True, index=True)
    description: str
    work_center: str
    created_by: Optional[int] = Field(default=None, foreign_key="employees.id")
    
    def __repr__(self) -> str:
        return f"Machine(code={self.machine_code})"
    
    def __str__(self) -> str:
        return f"{self.machine_code} - {self.description}"


class ActivityCode(SQLModel, table=True):
    """Activity definitions with standards"""
    
    __tablename__ = "activity_codes"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(unique=True, index=True)
    description: str
    std_hours_per_unit: Optional[float] = None
    std_qty_per_hour: Optional[float] = None
    efficiency_type: EfficiencyTypeEnum
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[int] = Field(default=None, foreign_key="employees.id")
    
    def __repr__(self) -> str:
        return f"ActivityCode(code={self.code})"
    
    def __str__(self) -> str:
        return f"{self.code} - {self.description}"


class WorkOrder(SQLModel, table=True):
    """Work order master"""
    
    __tablename__ = "work_orders"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    wo_number: str = Field(unique=True, index=True)
    machine_id: int = Field(foreign_key="machines.id")
    planned_qty: float
    msd_month: str  # Format: YYYY-MM
    created_by: Optional[int] = Field(default=None, foreign_key="employees.id")
    
    def __repr__(self) -> str:
        return f"WorkOrder(wo={self.wo_number})"
    
    def __str__(self) -> str:
        return f"WO {self.wo_number}"


class JobCard(SQLModel, table=True):
    """Job card transactions - core data table"""
    
    __tablename__ = "job_cards"
    __table_args__ = (
        Index("ix_jobcard_wo_machine", "work_order_id", "machine_id"),
        Index("ix_jobcard_entry_date", "entry_date"),
    )
    
    id: Optional[int] = Field(default=None, primary_key=True)
    employee_id: Optional[int] = Field(default=None, foreign_key="employees.id")
    supervisor_id: Optional[int] = Field(default=None, foreign_key="employees.id")
    machine_id: Optional[int] = Field(default=None, foreign_key="machines.id")
    work_order_id: Optional[int] = Field(default=None, foreign_key="work_orders.id")
    # Optional manual overrides for task-based/AWC entries when no master data exists
    manual_machine_text: Optional[str] = Field(default=None)
    manual_work_order_text: Optional[str] = Field(default=None)
    activity_code_id: Optional[int] = Field(default=None, foreign_key="activity_codes.id")
    activity_desc: str
    qty: float
    actual_hours: float
    status: JobCardStatusEnum
    entry_date: date
    source: SourceEnum
    shift: Optional[int] = Field(None, description="Shift: 1, 2, or 3")
    is_awc: bool = Field(default=False)
    approval_status: ApprovalStatusEnum = Field(default=ApprovalStatusEnum.PENDING)
    supervisor_remarks: Optional[str] = Field(default=None)
    approved_at: Optional[datetime] = Field(default=None)
    approved_by: Optional[int] = Field(default=None, foreign_key="employees.id")
    
    def __repr__(self) -> str:
        return f"JobCard(id={self.id}, wo={self.work_order_id})"
    
    def __str__(self) -> str:
        return f"JC#{self.id} - {self.activity_desc}"


class ValidationFlag(SQLModel, table=True):
    """Data validation flags"""
    
    __tablename__ = "validation_flags"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    job_card_id: int = Field(foreign_key="job_cards.id")
    flag_type: FlagTypeEnum
    details: str
    resolved: bool = Field(default=False)
    resolved_by: Optional[int] = Field(default=None, foreign_key="employees.id")
    
    def __repr__(self) -> str:
        return f"ValidationFlag(type={self.flag_type}, resolved={self.resolved})"
    
    def __str__(self) -> str:
        return f"{self.flag_type.value}: {self.details}"


class EfficiencyPeriod(SQLModel, table=True):
    """Aggregated efficiency metrics by period"""
    
    __tablename__ = "efficiency_periods"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    employee_id: int = Field(foreign_key="employees.id")
    period_start: date
    period_end: date
    time_efficiency: Optional[float] = None
    task_efficiency: Optional[float] = None
    quantity_efficiency: Optional[float] = None
    awc_pct: float
    standard_hours_allowed: float
    actual_hours: float
    
    def __repr__(self) -> str:
        return f"EfficiencyPeriod(emp={self.employee_id}, {self.period_start}-{self.period_end})"
    
    def __str__(self) -> str:
        return f"Period {self.period_start} to {self.period_end}"


class AuditLog(SQLModel, table=True):
    """Audit trail for supervisor actions"""
    
    __tablename__ = "audit_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    action_type: str  # "assign", "resolve_flag", etc.
    performed_by: int = Field(foreign_key="employees.id")
    target_id: Optional[int] = None  # ID of affected entity (jobcard, flag, etc.)
    details: str  # JSON or text description
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"AuditLog(action={self.action_type}, by={self.performed_by})"
    
    def __str__(self) -> str:
        return f"{self.action_type} by user {self.performed_by} at {self.timestamp}"
