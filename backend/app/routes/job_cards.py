"""
Job Cards CRUD routes with validation engine integration.
"""

from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func

from app.core.database import get_async_session
from app.core.security import get_current_user, require_roles
from app.models.models import (
    JobCard,
    ValidationFlag,
    Machine,
    WorkOrder,
    ActivityCode,
    JobCardStatusEnum,
    SourceEnum,
    ApprovalStatusEnum,
)
from app.models.employee import Employee
from app.schemas.job_card_schemas import (
    JobCardCreate,
    JobCardRead,
    JobCardUpdate,
    JobCardWithDetails,
)
from app.services.validation_engine import ValidationEngine, validate_job_card, revalidate_job_card

router = APIRouter()


@router.post("/", response_model=JobCardRead, status_code=status.HTTP_201_CREATED)
async def create_job_card(
    job_card_data: JobCardCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(get_current_user),
):
    """
    Create a new job card (Operator or Supervisor).
    
    Validates:
    - Machine exists
    - Work order exists
    - Activity code exists (if provided)
    - Employee exists (if provided)
    
    After creation, runs validation engine to detect issues.
    """
    # Verify machine/work order depending on AWC (TASK_BASED) and presence of IDs
    if job_card_data.machine_id is not None:
        machine = await session.get(Machine, job_card_data.machine_id)
        if not machine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Machine with ID {job_card_data.machine_id} not found"
            )
    elif not getattr(job_card_data, "is_awc", False):
        # For non-AWC (non task-based) machine_id is required
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="machine_id is required for non task-based job cards"
        )

    if job_card_data.work_order_id is not None:
        work_order = await session.get(WorkOrder, job_card_data.work_order_id)
        if not work_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work order with ID {job_card_data.work_order_id} not found"
            )
    elif not getattr(job_card_data, "is_awc", False):
        # For non-AWC (non task-based) work_order_id is required
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="work_order_id is required for non task-based job cards"
        )
    
    activity_code = None

    # Verify activity code if provided
    if job_card_data.activity_code_id:
        activity_code = await session.get(ActivityCode, job_card_data.activity_code_id)
        if not activity_code:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Activity code with ID {job_card_data.activity_code_id} not found"
            )
    
    # Verify employee if provided
    if job_card_data.employee_id:
        employee = await session.get(Employee, job_card_data.employee_id)
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee with ID {job_card_data.employee_id} not found"
            )

    # Authorization/validation for operator submissions
    if current_user.role.value == "OPERATOR":
        # Operators can only submit job cards for themselves
        if job_card_data.employee_id is not None and job_card_data.employee_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operators can only create job cards for themselves",
            )

        # Operator module is inherited from the supervisor who created them
        if current_user.created_by is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operator is not assigned to a supervisor",
            )

        creator = await session.get(Employee, current_user.created_by)
        if not creator or creator.role.value != "SUPERVISOR":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operator's creator is not a supervisor",
            )

        required_module = getattr(creator, "supervisor_efficiency_module", None)
        if required_module is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Supervisor efficiency module is not configured",
            )

        # Derive job card module from AWC flag or activity code
        if getattr(job_card_data, "is_awc", False):
            job_card_module = "TASK_BASED"
        elif activity_code and getattr(activity_code, "efficiency_type", None) is not None:
            job_card_module = (
                activity_code.efficiency_type.value
                if hasattr(activity_code.efficiency_type, "value")
                else str(activity_code.efficiency_type)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="activity_code_id is required for non task-based job cards",
            )

        required_module_value = required_module.value if hasattr(required_module, "value") else str(required_module)
        if job_card_module != required_module_value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Operators created under a {required_module_value} supervisor can submit only "
                    f"{required_module_value} job cards"
                ),
            )
    
    # Verify supervisor if provided
    if job_card_data.supervisor_id:
        supervisor = await session.get(Employee, job_card_data.supervisor_id)
        if not supervisor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Supervisor with ID {job_card_data.supervisor_id} not found"
            )
    
    # Convert enums
    try:
        status_enum = JobCardStatusEnum(job_card_data.status)
        source_enum = SourceEnum(job_card_data.source)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    job_card_fields = job_card_data.model_dump(exclude={'status', 'source'})

    # If operator, force employee_id and default supervisor_id to creator supervisor
    if current_user.role.value == "OPERATOR":
        job_card_fields["employee_id"] = current_user.id
        job_card_fields["supervisor_id"] = job_card_fields.get("supervisor_id") or current_user.created_by

    # Create job card
    job_card = JobCard(
        **job_card_fields,
        status=status_enum,
        source=source_enum,
    )
    
    session.add(job_card)
    await session.commit()
    await session.refresh(job_card)
    
    # Run validation engine (async)
    engine = ValidationEngine()
    validation_flags = await engine.run_for_jobcard(job_card, session)
    # Flags are already committed by the engine
    
    return job_card


@router.get("/", response_model=List[JobCardWithDetails])
async def list_job_cards(
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[date] = Query(None, description="Filter by start date (inclusive)"),
    end_date: Optional[date] = Query(None, description="Filter by end date (inclusive)"),
    employee_id: Optional[int] = Query(None, description="Filter by employee ID"),
    source: Optional[str] = Query(None, description="Filter by source: TECHNICIAN or SUPERVISOR"),
    approval_status: Optional[str] = Query(None, description="Filter by approval status: PENDING, APPROVED, REJECTED"),
    has_flags: Optional[bool] = Query(None, description="Filter by validation flag presence"),
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(get_current_user),
):
    """
    List job cards with optional filters.
    
    Filters:
    - start_date: Filter entries >= this date
    - end_date: Filter entries <= this date
    - employee_id: Filter by employee
    - has_flags: Filter by presence of validation flags
    """
    # Build base query with joins
    from sqlalchemy.orm import aliased
    EmployeeAlias = aliased(Employee)
    ApproverAlias = aliased(Employee)
    
    statement = select(
        JobCard,
        EmployeeAlias,  # Employee who created the job card
        Machine,
        WorkOrder,
        ActivityCode,
        ApproverAlias,  # Supervisor who approved/rejected
    ).outerjoin(
        EmployeeAlias, JobCard.employee_id == EmployeeAlias.id
    ).outerjoin(
        Machine, JobCard.machine_id == Machine.id
    ).outerjoin(
        WorkOrder, JobCard.work_order_id == WorkOrder.id
    ).outerjoin(
        ActivityCode, JobCard.activity_code_id == ActivityCode.id
    ).outerjoin(
        ApproverAlias, JobCard.approved_by == ApproverAlias.id
    )
    
    # Apply date filters
    if start_date:
        statement = statement.where(JobCard.entry_date >= start_date)
    if end_date:
        statement = statement.where(JobCard.entry_date <= end_date)
    
    # Scope for operator: force to own records
    effective_employee_id = employee_id
    if current_user.role.value == "OPERATOR":
        effective_employee_id = current_user.id
    
    # Apply employee filter
    if effective_employee_id:
        statement = statement.where(JobCard.employee_id == effective_employee_id)
    
    # Apply source filter
    if source:
        try:
            src_enum = SourceEnum(source)
            statement = statement.where(JobCard.source == src_enum)
        except ValueError:
            pass
    
    # Apply approval status filter
    if approval_status:
        try:
            appr_enum = ApprovalStatusEnum(approval_status)
            statement = statement.where(JobCard.approval_status == appr_enum)
        except ValueError:
            pass
    
    statement = statement.offset(skip).limit(limit)
    result = await session.execute(statement)
    results = result.all()
    
    # Build response with details
    job_cards = []
    for jc, emp, machine, wo, activity, approver in results:
        # Check if has flags
        flag_statement = select(ValidationFlag).where(
            ValidationFlag.job_card_id == jc.id,
            ValidationFlag.resolved == False
        )
        flag_result = await session.execute(flag_statement)
        has_flag = flag_result.first() is not None
        
        # Apply flag filter if specified
        if has_flags is not None and has_flag != has_flags:
            continue
        
        # Get supervisor name if exists
        supervisor_name = None
        if jc.supervisor_id:
            supervisor = await session.get(Employee, jc.supervisor_id)
            supervisor_name = supervisor.name if supervisor else None

        # Derive efficiency module from activity code or AWC flag
        efficiency_module: Optional[str] = None
        if activity and getattr(activity, "efficiency_type", None) is not None:
            efficiency_module = activity.efficiency_type.value if hasattr(activity.efficiency_type, "value") else str(activity.efficiency_type)
        elif getattr(jc, "is_awc", False):
            # Treat AWC entries as TASK_BASED module for grouping purposes
            efficiency_module = "TASK_BASED"
        
        job_cards.append(
            JobCardWithDetails(
                id=jc.id,
                employee_id=jc.employee_id,
                supervisor_id=jc.supervisor_id,
                machine_id=jc.machine_id,
                work_order_id=jc.work_order_id,
                activity_code_id=jc.activity_code_id,
                activity_desc=(activity.description if activity and getattr(activity, "description", None) else jc.activity_desc),
                qty=jc.qty,
                actual_hours=jc.actual_hours,
                status=jc.status.value,
                entry_date=jc.entry_date,
                source=jc.source.value,
                employee_name=emp.name if emp else None,
                supervisor_name=supervisor_name,
                machine_code=machine.machine_code if machine else None,
                wo_number=wo.wo_number if wo else None,
                activity_code=activity.code if activity else None,
                efficiency_module=efficiency_module,
                has_flags=has_flag,
                approval_status=jc.approval_status.value if jc.approval_status else None,
                supervisor_remarks=jc.supervisor_remarks,
                approved_at=jc.approved_at.isoformat() if jc.approved_at else None,
                approved_by_name=approver.name if approver else None,
                std_hours_per_unit=activity.std_hours_per_unit if activity else None,
                std_qty_per_hour=activity.std_qty_per_hour if activity else None,
            )
        )
    
    return job_cards


@router.get("/{job_card_id}", response_model=JobCardRead)
async def get_job_card(
    job_card_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(get_current_user),
):
    """Get a single job card by ID."""
    job_card = await session.get(JobCard, job_card_id)
    if not job_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job card not found"
        )
    # Return schema-friendly data (convert enums to strings)
    return JobCardRead(
        id=job_card.id,
        employee_id=job_card.employee_id,
        supervisor_id=job_card.supervisor_id,
        machine_id=job_card.machine_id,
        work_order_id=job_card.work_order_id,
        activity_code_id=job_card.activity_code_id,
        activity_desc=job_card.activity_desc,
        qty=job_card.qty,
        actual_hours=job_card.actual_hours,
        shift=getattr(job_card, 'shift', None),
        is_awc=getattr(job_card, 'is_awc', False),
        status=job_card.status.value if job_card.status else None,
        entry_date=job_card.entry_date,
        source=job_card.source.value if job_card.source else None,
        approval_status=job_card.approval_status.value if job_card.approval_status else "PENDING",
        supervisor_remarks=job_card.supervisor_remarks,
        approved_at=job_card.approved_at,
        approved_by=job_card.approved_by,
    )


@router.patch("/{job_card_id}", response_model=JobCardRead)
async def update_job_card(
    job_card_id: int,
    job_card_data: JobCardUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(get_current_user),
):
    """
    Update a job card (Supervisor only).
    
    After update, re-runs validation engine to update flags.
    """
    job_card = await session.get(JobCard, job_card_id)
    if not job_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job card not found"
        )
    
    # Verify references if being updated
    if job_card_data.machine_id:
        machine = await session.get(Machine, job_card_data.machine_id)
        if not machine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Machine with ID {job_card_data.machine_id} not found"
            )
    
    if job_card_data.work_order_id:
        work_order = await session.get(WorkOrder, job_card_data.work_order_id)
        if not work_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work order with ID {job_card_data.work_order_id} not found"
            )
    
    if job_card_data.activity_code_id:
        activity_code = await session.get(ActivityCode, job_card_data.activity_code_id)
        if not activity_code:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Activity code with ID {job_card_data.activity_code_id} not found"
            )
    
    if job_card_data.employee_id:
        employee = await session.get(Employee, job_card_data.employee_id)
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee with ID {job_card_data.employee_id} not found"
            )
    
    # Authorization: allow Admin/Supervisor, or Operator can edit own job card if not approved yet
    is_admin_or_supervisor = current_user.role.value in ["ADMIN", "SUPERVISOR"]
    if not is_admin_or_supervisor:
        # Operator path: can edit own job cards unless already approved
        if job_card.employee_id != current_user.id or job_card.approval_status == ApprovalStatusEnum.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins/supervisors or the owner may edit before approval",
            )

    # Convert enums if provided
    status_enum = None
    source_enum = None
    
    if job_card_data.status:
        try:
            status_enum = JobCardStatusEnum(job_card_data.status)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    if job_card_data.source:
        try:
            source_enum = SourceEnum(job_card_data.source)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    # Update fields
    update_data = job_card_data.model_dump(exclude_unset=True, exclude={'status', 'source'})

    # If operator, restrict editable fields to safe subset
    if not is_admin_or_supervisor:
        allowed_fields = {
            'machine_id',
            'work_order_id',
            'activity_code_id',
            'activity_desc',
            'qty',
            'actual_hours',
            'entry_date',
            'source',
            'shift',
            'is_awc',
        }
        update_data = {k: v for k, v in update_data.items() if k in allowed_fields}
    for key, value in update_data.items():
        setattr(job_card, key, value)
    
    if status_enum:
        job_card.status = status_enum
    if source_enum:
        job_card.source = source_enum
    
    # Reset approval status to pending when job card is edited
    job_card.approval_status = ApprovalStatusEnum.PENDING
    job_card.supervisor_remarks = None
    job_card.approved_at = None
    job_card.approved_by = None
    
    session.add(job_card)
    await session.commit()
    await session.refresh(job_card)
    
    # Re-run validation engine (async)
    engine = ValidationEngine()
    await engine.run_for_jobcard(job_card, session)
    # Flags are already committed by the engine
    
    return job_card


@router.delete("/{job_card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job_card(
    job_card_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(require_roles(["ADMIN"])),
):
    """Delete a job card (Admin only)."""
    job_card = await session.get(JobCard, job_card_id)
    if not job_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job card not found"
        )
    
    await session.delete(job_card)
    await session.commit()
    return None
