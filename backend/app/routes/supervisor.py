"""
Supervisor tools routes.
Provides assignment, validation management, and audit capabilities.
"""

import json
from typing import List, Optional
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_async_session
from app.core.security import require_roles
from app.models.models import (
    JobCard,
    WorkOrder,
    ActivityCode,
    Machine,
    ValidationFlag,
    AuditLog,
    JobCardStatusEnum,
    SourceEnum,
    FlagTypeEnum,
    ApprovalStatusEnum,
)
from app.models.employee import Employee
from app.schemas.supervisor_schemas import (
    AssignWorkRequest,
    AssignWorkResponse,
    ValidationFlagDetail,
    ResolveValidationRequest,
    ResolveValidationResponse,
)
from app.schemas.job_card_schemas import (
    JobCardReview,
    SupervisorApprovalRequest,
    SupervisorApprovalResponse,
)
from app.services.validation_engine import ValidationEngine
from app.services.efficiency_engine import compute_employee_efficiency

router = APIRouter()


# ============================================================================
# POST /assign - Work Assignment
# ============================================================================

@router.post("/assign", response_model=AssignWorkResponse)
async def assign_work(
    request: AssignWorkRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(require_roles(["SUPERVISOR", "ADMIN"])),
) -> AssignWorkResponse:
    """
    Assign work to employees and create jobcards.
    
    Modes:
    - manual: Use provided assignments list as-is
    - auto_split_hours: Automatically distribute hours equally among team members
    
    Creates jobcards with source=SUPERVISOR and logs the action.
    """
    # Verify work order exists
    work_order = await session.get(WorkOrder, request.work_order_id)
    if not work_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Work order {request.work_order_id} not found"
        )
    
    # Verify activity code exists
    activity_code = await session.get(ActivityCode, request.activity_code_id)
    if not activity_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Activity code {request.activity_code_id} not found"
        )
    
    # Get machine from work order
    machine = await session.get(Machine, work_order.machine_id)
    
    # Determine assignments based on mode
    if request.mode == "auto_split_hours":
        assignments = await _auto_split_hours(
            current_user.supervisor_efficiency_module,
            request.assignments,
            session
        )
    else:
        assignments = request.assignments
    
    # Validate all employees exist
    for assignment in assignments:
        employee = await session.get(Employee, assignment.employee_id)
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee {assignment.employee_id} not found"
            )
    
    # Create jobcards (initially incomplete until operator submits)
    created_ids = []
    for assignment in assignments:
        jobcard = JobCard(
            employee_id=assignment.employee_id,
            supervisor_id=current_user.id,
            machine_id=work_order.machine_id,
            work_order_id=request.work_order_id,
            activity_code_id=request.activity_code_id,
            activity_desc=activity_code.description,
            qty=assignment.qty,
            actual_hours=assignment.hours,
            status=JobCardStatusEnum.IC,
            entry_date=request.entry_date,
            source=SourceEnum.SUPERVISOR,
        )
        session.add(jobcard)
        await session.flush()
        await session.refresh(jobcard)
        created_ids.append(jobcard.id)
        
        # Run validation engine on each jobcard
        engine = ValidationEngine()
        await engine.run_for_jobcard(jobcard, session)
    
    # Create audit log
    audit_log = AuditLog(
        action_type="assign_work",
        performed_by=current_user.id,
        target_id=request.work_order_id,
        details=json.dumps({
            "work_order_id": request.work_order_id,
            "activity_code_id": request.activity_code_id,
            "mode": request.mode,
            "assignments_count": len(assignments),
            "created_jobcards": created_ids,
        }),
    )
    session.add(audit_log)
    await session.commit()
    await session.refresh(audit_log)
    
    return AssignWorkResponse(
        created_jobcards=created_ids,
        audit_log_id=audit_log.id,
    )


async def _auto_split_hours(
    efficiency_module: Optional[str],
    assignments: List,
    session: AsyncSession,
) -> List:
    """
    Auto-split hours equally among team members.
    
    If assignments list is provided, use those employee IDs.
    Otherwise, fetch all active employees in the same efficiency module.
    """
    if not assignments:
        # Fetch employees in the same efficiency module if no assignments provided
        if not efficiency_module:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No efficiency module assigned to supervisor for auto-split"
            )
        
        stmt = select(Employee).where(
            Employee.is_active == True,
            Employee.role == "OPERATOR"
        )
        result = await session.execute(stmt)
        employees = result.scalars().all()
        
        if not employees:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No active operators found in the efficiency module {efficiency_module}"
            )
        
        # Create equal assignments (you'd calculate actual splits based on total hours)
        # For now, return empty list as we're not implementing auto-split yet
        return []
    
    # Equal distribution of hours and qty among provided employees
    total_hours = sum(a.hours for a in assignments)
    total_qty = sum(a.qty for a in assignments)
    n = len(assignments)
    
    hours_per_person = total_hours / n
    qty_per_person = total_qty / n
    
    from app.schemas.supervisor_schemas import AssignmentItem
    return [
        AssignmentItem(
            employee_id=a.employee_id,
            hours=hours_per_person,
            qty=qty_per_person,
        )
        for a in assignments
    ]


# ============================================================================
# GET /validations - List Validation Flags
# ============================================================================

@router.get("/validations", response_model=List[ValidationFlagDetail])
async def list_validations(
    flag_type: Optional[str] = Query(None, description="Filter by flag type"),
    resolved: Optional[bool] = Query(None, description="Filter by resolved status"),
    start_date: Optional[date] = Query(None, description="Filter jobcards >= this date"),
    end_date: Optional[date] = Query(None, description="Filter jobcards <= this date"),
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(require_roles(["SUPERVISOR", "ADMIN"])),
) -> List[ValidationFlagDetail]:
    """
    List validation flags with filters and jobcard details.
    
    Filters:
    - flag_type: DUPLICATION, OUTSIDE_MSD, AWC, SPLIT_CANDIDATE, QTY_MISMATCH
    - resolved: true/false
    - start_date/end_date: Filter by jobcard entry_date
    """
    # Build query
    stmt = (
        select(ValidationFlag, JobCard, Employee, Machine, WorkOrder, ActivityCode)
        .join(JobCard, ValidationFlag.job_card_id == JobCard.id)
        .outerjoin(Employee, JobCard.employee_id == Employee.id)
        .join(Machine, JobCard.machine_id == Machine.id)
        .join(WorkOrder, JobCard.work_order_id == WorkOrder.id)
        .outerjoin(ActivityCode, JobCard.activity_code_id == ActivityCode.id)
    )
    
    # Apply filters
    if flag_type:
        try:
            flag_enum = FlagTypeEnum(flag_type)
            stmt = stmt.where(ValidationFlag.flag_type == flag_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid flag_type: {flag_type}"
            )
    
    if resolved is not None:
        stmt = stmt.where(ValidationFlag.resolved == resolved)
    
    if start_date:
        stmt = stmt.where(JobCard.entry_date >= start_date)
    
    if end_date:
        stmt = stmt.where(JobCard.entry_date <= end_date)
    
    stmt = stmt.offset(skip).limit(limit)
    
    result = await session.execute(stmt)
    rows = result.all()
    
    # Build response
    flags = []
    for flag, jc, emp, machine, wo, activity in rows:
        flags.append(
            ValidationFlagDetail(
                flag_id=flag.id,
                job_card_id=jc.id,
                flag_type=flag.flag_type.value,
                details=flag.details,
                resolved=flag.resolved,
                resolved_by=flag.resolved_by,
                employee_id=emp.id if emp else None,
                employee_name=emp.name if emp else None,
                machine_code=machine.machine_code,
                wo_number=wo.wo_number,
                activity_code=activity.code if activity else None,
                entry_date=jc.entry_date,
                actual_hours=jc.actual_hours,
                qty=jc.qty,
            )
        )
    
    return flags


# ============================================================================
# PATCH /validations/{flag_id}/resolve - Resolve Validation Flag
# ============================================================================

@router.patch("/validations/{flag_id}/resolve", response_model=ResolveValidationResponse)
async def resolve_validation(
    flag_id: int,
    request: ResolveValidationRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(require_roles(["SUPERVISOR", "ADMIN"])),
) -> ResolveValidationResponse:
    """
    Mark a validation flag as resolved.
    
    Only SUPERVISOR or ADMIN can resolve flags.
    Creates audit log entry.
    """
    # Fetch flag
    flag = await session.get(ValidationFlag, flag_id)
    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Validation flag {flag_id} not found"
        )
    
    if flag.resolved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Flag already resolved"
        )
    
    # Mark as resolved
    flag.resolved = True
    flag.resolved_by = current_user.id
    session.add(flag)
    
    # Create audit log
    audit_log = AuditLog(
        action_type="resolve_flag",
        performed_by=current_user.id,
        target_id=flag_id,
        details=json.dumps({
            "flag_id": flag_id,
            "flag_type": flag.flag_type.value,
            "job_card_id": flag.job_card_id,
            "comment": request.comment or "",
        }),
    )
    session.add(audit_log)
    
    await session.commit()
    await session.refresh(audit_log)
    
    return ResolveValidationResponse(
        flag_id=flag_id,
        resolved=True,
        resolved_by=current_user.id,
        audit_log_id=audit_log.id,
    )


# ============================================================================
# GET /jobcards/review - List Job Cards for Supervisor Review
# ============================================================================

@router.get("/jobcards/review", response_model=List[JobCardReview])
async def list_jobcards_for_review(
    efficiency_module: Optional[str] = Query(None, description="Filter by efficiency module: TIME_BASED, QUANTITY_BASED, TASK_BASED"),
    approval_status: Optional[str] = Query(None, description="Filter by approval status: PENDING, APPROVED, REJECTED"),
    start_date: Optional[date] = Query(None, description="Filter by start date (inclusive)"),
    end_date: Optional[date] = Query(None, description="Filter by end date (inclusive)"),
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(require_roles(["SUPERVISOR", "ADMIN"])),
) -> List[JobCardReview]:
    """
    List job cards for supervisor review with filters.

    Filters:
    - efficiency_module: Filter by activity efficiency type
    - approval_status: Filter by current approval status (if not provided, returns all statuses)
    - start_date/end_date: Filter by entry_date
    """
    # Build query
    stmt = (
        select(JobCard, Employee, Machine, WorkOrder, ActivityCode)
        .outerjoin(Employee, JobCard.employee_id == Employee.id)
        .outerjoin(Machine, JobCard.machine_id == Machine.id)
        .outerjoin(WorkOrder, JobCard.work_order_id == WorkOrder.id)
        .outerjoin(ActivityCode, JobCard.activity_code_id == ActivityCode.id)
    )

    # Apply filters
    # Only review job cards that have been submitted by operators (completed)
    stmt = stmt.where(JobCard.status == JobCardStatusEnum.C)
    if efficiency_module:
        try:
            from app.models.models import EfficiencyTypeEnum
            eff_enum = EfficiencyTypeEnum(efficiency_module)
            stmt = stmt.where(ActivityCode.efficiency_type == eff_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid efficiency_module: {efficiency_module}"
            )

    if approval_status and approval_status != "ALL":
        try:
            approval_enum = ApprovalStatusEnum(approval_status)
            stmt = stmt.where(JobCard.approval_status == approval_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid approval_status: {approval_status}"
            )

    if start_date:
        stmt = stmt.where(JobCard.entry_date >= start_date)

    if end_date:
        stmt = stmt.where(JobCard.entry_date <= end_date)

    stmt = stmt.offset(skip).limit(limit)

    result = await session.execute(stmt)
    rows = result.all()

    # Build response
    jobcards = []
    for jc, emp, machine, wo, activity in rows:
        # Determine efficiency module (from activity code if available)
        efficiency_module_display = "UNKNOWN"
        if activity and activity.efficiency_type:
            efficiency_module_display = activity.efficiency_type.value
        elif getattr(jc, "is_awc", False):  # If it's AWC and no activity code, assume TASK_BASED
            efficiency_module_display = "TASK_BASED"

        # Check if has flags
        flag_statement = select(ValidationFlag).where(
            ValidationFlag.job_card_id == jc.id,
            ValidationFlag.resolved == False
        )
        flag_result = await session.execute(flag_statement)
        has_flag = flag_result.first() is not None

        jobcards.append(
            JobCardReview(
                id=jc.id,
                employee_id=emp.id if emp else None,
                employee_name=emp.name if emp else None,
                employee_ec_number=emp.ec_number if emp else None,
                machine_code=machine.machine_code if machine else "",
                wo_number=wo.wo_number if wo else "",
                activity_desc=(activity.description if activity and getattr(activity, "description", None) else jc.activity_desc),
                activity_code=activity.code if activity else None,
                efficiency_module=efficiency_module_display,
                qty=jc.qty,
                actual_hours=jc.actual_hours,
                status=jc.status.value,
                entry_date=jc.entry_date.isoformat(),
                shift=(jc.shift or 1),  # Default to shift 1 if not set
                approval_status=jc.approval_status.value,
                has_flags=has_flag,
                std_hours_per_unit=activity.std_hours_per_unit if activity else None,
                std_qty_per_hour=activity.std_qty_per_hour if activity else None,
            )
        )

    return jobcards


# ============================================================================
# POST /jobcards/{job_card_id}/approve - Approve/Reject Job Card
# ============================================================================

@router.post("/jobcards/{job_card_id}/approve", response_model=SupervisorApprovalResponse)
async def approve_job_card(
    job_card_id: int,
    request: SupervisorApprovalRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(require_roles(["SUPERVISOR", "ADMIN"])),
) -> SupervisorApprovalResponse:
    """
    Approve or reject a job card.

    Only SUPERVISOR or ADMIN can approve/reject job cards.
    Creates audit log entry.
    """
    # Fetch job card
    job_card = await session.get(JobCard, job_card_id)
    if not job_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job card {job_card_id} not found"
        )

    if job_card.approval_status != ApprovalStatusEnum.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job card has already been reviewed"
        )

    # Update approval status
    from datetime import datetime
    now = datetime.utcnow()

    if request.action == "APPROVE":
        job_card.approval_status = ApprovalStatusEnum.APPROVED
    elif request.action == "REJECT":
        job_card.approval_status = ApprovalStatusEnum.REJECTED
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid action"
        )

    job_card.supervisor_remarks = request.remarks
    job_card.approved_at = now
    job_card.approved_by = current_user.id

    session.add(job_card)

    # Create audit log
    audit_log = AuditLog(
        action_type="approve_jobcard" if request.action == "APPROVE" else "reject_jobcard",
        performed_by=current_user.id,
        target_id=job_card_id,
        details=json.dumps({
            "job_card_id": job_card_id,
            "action": request.action,
            "remarks": request.remarks or "",
        }),
    )
    session.add(audit_log)

    await session.commit()
    await session.refresh(audit_log)

    # Recompute EfficiencyPeriod for this employee for the month-to-date of the job card date
    try:
        jc_date = job_card.entry_date
        period_start = jc_date.replace(day=1)
        # Compute month end and clamp to today to align with dashboard summary (end=today)
        if jc_date.month == 12:
            from datetime import date as _date
            month_end = _date(jc_date.year + 1, 1, 1) - timedelta(days=1)
        else:
            from datetime import date as _date
            month_end = _date(jc_date.year, jc_date.month + 1, 1) - timedelta(days=1)
        from datetime import date as _date
        today = _date.today()
        period_end = today if today <= month_end else month_end
        await compute_employee_efficiency(job_card.employee_id, period_start, period_end, session)
    except Exception:
        # Non-fatal: do not block approval if recompute fails
        pass

    return SupervisorApprovalResponse(
        job_card_id=job_card_id,
        approval_status=job_card.approval_status.value,
        approved_by=current_user.id,
        approved_at=now.isoformat(),
        remarks=request.remarks,
    )
