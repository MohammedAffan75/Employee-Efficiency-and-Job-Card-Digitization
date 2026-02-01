"""
Activity Codes CRUD routes (Admin only).
"""

from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.security import require_roles
from app.models.models import ActivityCode, EfficiencyTypeEnum
from app.models.employee import Employee
from app.schemas.activity_code_schemas import (
    ActivityCodeCreate,
    ActivityCodeRead,
    ActivityCodeUpdate,
)

router = APIRouter()


@router.get("/", response_model=List[ActivityCodeRead])
def list_activity_codes(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: Employee = Depends(require_roles(["ADMIN", "SUPERVISOR", "OPERATOR"])),
):
    """
    List all activity codes (All roles).
    
    Supervisors: only see codes they created, and only within their assigned module.
    Supports pagination with skip and limit parameters.
    """
    statement = select(ActivityCode)
    if current_user.role == "SUPERVISOR":
        statement = statement.where(
            (ActivityCode.created_by == current_user.id)
            & (ActivityCode.efficiency_type == current_user.supervisor_efficiency_module)
        )
    statement = statement.offset(skip).limit(limit)
    activity_codes = session.exec(statement).all()
    return activity_codes


@router.get("/{activity_code_id}", response_model=ActivityCodeRead)
def get_activity_code(
    activity_code_id: int,
    session: Session = Depends(get_session),
    current_user: Employee = Depends(require_roles(["ADMIN", "SUPERVISOR", "OPERATOR"])),
):
    """Get a single activity code by ID (All roles)."""
    activity_code = session.get(ActivityCode, activity_code_id)
    if not activity_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity code not found"
        )
    return activity_code


@router.post("/", response_model=ActivityCodeRead, status_code=status.HTTP_201_CREATED)
def create_activity_code(
    activity_code_data: ActivityCodeCreate,
    session: Session = Depends(get_session),
    current_user: Employee = Depends(require_roles(["SUPERVISOR"])),
):
    """
    Create a new activity code (Supervisor only).
    
    Validates that:
    - Code is unique
    - Efficiency type is valid
    """
    # Check if code already exists
    statement = select(ActivityCode).where(ActivityCode.code == activity_code_data.code)
    existing = session.exec(statement).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Activity code '{activity_code_data.code}' already exists"
        )
    
    # Determine efficiency type
    if current_user.role == "SUPERVISOR":
        if not current_user.supervisor_efficiency_module:
            raise HTTPException(status_code=400, detail="Supervisor has no assigned efficiency module")
        efficiency_type = current_user.supervisor_efficiency_module
    else:
        try:
            efficiency_type = EfficiencyTypeEnum(activity_code_data.efficiency_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid efficiency type. Must be one of: {', '.join([e.value for e in EfficiencyTypeEnum])}"
            )
    
    # Create activity code
    payload = activity_code_data.model_dump(exclude={"efficiency_type"})
    activity_code = ActivityCode(
        **payload,
        efficiency_type=efficiency_type,
        last_updated=datetime.utcnow(),
        created_by=current_user.id if current_user.role == "SUPERVISOR" else None,
    )
    
    session.add(activity_code)
    session.commit()
    session.refresh(activity_code)
    return activity_code


@router.patch("/{activity_code_id}", response_model=ActivityCodeRead)
def update_activity_code(
    activity_code_id: int,
    activity_code_data: ActivityCodeUpdate,
    session: Session = Depends(get_session),
    current_user: Employee = Depends(require_roles(["SUPERVISOR"])),
):
    """Update an activity code (Supervisor only)."""
    activity_code = session.get(ActivityCode, activity_code_id)
    if not activity_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity code not found"
        )
    
    # Check code uniqueness if being updated
    if activity_code_data.code and activity_code_data.code != activity_code.code:
        statement = select(ActivityCode).where(ActivityCode.code == activity_code_data.code)
        existing = session.exec(statement).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Activity code '{activity_code_data.code}' already exists"
            )
    
    # Validate efficiency type if being updated
    if activity_code_data.efficiency_type:
        try:
            efficiency_type = EfficiencyTypeEnum(activity_code_data.efficiency_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid efficiency type. Must be one of: {', '.join([e.value for e in EfficiencyTypeEnum])}"
            )
    
    # Update fields
    update_data = activity_code_data.model_dump(exclude_unset=True, exclude={'efficiency_type'})
    for key, value in update_data.items():
        setattr(activity_code, key, value)
    
    if activity_code_data.efficiency_type:
        activity_code.efficiency_type = efficiency_type
    
    activity_code.last_updated = datetime.utcnow()
    
    session.add(activity_code)
    session.commit()
    session.refresh(activity_code)
    return activity_code


@router.delete("/{activity_code_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activity_code(
    activity_code_id: int,
    session: Session = Depends(get_session),
    current_user: Employee = Depends(require_roles(["SUPERVISOR"])),
):
    """Delete an activity code (Supervisor only)."""
    activity_code = session.get(ActivityCode, activity_code_id)
    if not activity_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity code not found"
        )

    # Check for dependencies before deletion
    from sqlmodel import select
    from app.models.models import JobCard

    # Check if activity code is used in job cards
    jc_stmt = select(JobCard).where(JobCard.activity_code_id == activity_code_id)
    job_cards = session.exec(jc_stmt).first()
    if job_cards:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete activity code '{activity_code.code}' - it is referenced by job cards. Remove associated job cards first."
        )

    session.delete(activity_code)
    session.commit()
    return None
