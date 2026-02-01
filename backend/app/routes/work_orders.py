"""
Work Orders CRUD routes (Supervisor + Admin).
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.security import require_roles
from app.models.models import WorkOrder, Machine
from app.models.employee import Employee
from app.schemas.work_order_schemas import (
    WorkOrderCreate,
    WorkOrderRead,
    WorkOrderUpdate,
    WorkOrderWithMachine,
)

router = APIRouter()


@router.get("/", response_model=List[WorkOrderWithMachine])
def list_work_orders(
    skip: int = 0,
    limit: int = 100,
    msd_month: Optional[str] = Query(None, description="Filter by MSD month (YYYY-MM)"),
    machine_id: Optional[int] = Query(None, description="Filter by machine ID"),
    session: Session = Depends(get_session),
    current_user: Employee = Depends(require_roles(["ADMIN", "SUPERVISOR", "OPERATOR"])),
):
    """
    List work orders with optional filters (All roles).
    
    Filters:
    - msd_month: Filter by MSD month (format: YYYY-MM)
    - machine_id: Filter by machine ID
    """
    statement = select(WorkOrder, Machine).join(Machine, WorkOrder.machine_id == Machine.id)
    
    # Apply filters
    if msd_month:
        statement = statement.where(WorkOrder.msd_month == msd_month)
    if machine_id:
        statement = statement.where(WorkOrder.machine_id == machine_id)
    
    if current_user.role == "SUPERVISOR":
        statement = statement.where(WorkOrder.created_by == current_user.id)
    statement = statement.offset(skip).limit(limit)
    results = session.exec(statement).all()
    
    # Build response with machine details
    work_orders = []
    for wo, machine in results:
        work_orders.append(
            WorkOrderWithMachine(
                id=wo.id,
                wo_number=wo.wo_number,
                machine_id=wo.machine_id,
                planned_qty=wo.planned_qty,
                msd_month=wo.msd_month,
                machine_code=machine.machine_code,
                machine_description=machine.description,
            )
        )
    
    return work_orders


@router.get("/{work_order_id}", response_model=WorkOrderRead)
def get_work_order(
    work_order_id: int,
    session: Session = Depends(get_session),
    current_user: Employee = Depends(require_roles(["ADMIN", "SUPERVISOR", "OPERATOR"])),
):
    """Get a single work order by ID (All roles)."""
    work_order = session.get(WorkOrder, work_order_id)
    if not work_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work order not found"
        )
    return work_order


@router.post("/", response_model=WorkOrderRead, status_code=status.HTTP_201_CREATED)
def create_work_order(
    work_order_data: WorkOrderCreate,
    session: Session = Depends(get_session),
    current_user: Employee = Depends(require_roles(["SUPERVISOR"])),
):
    """
    Create a new work order (Supervisor only).
    
    Validates:
    - WO number is unique
    - Machine exists
    - MSD month format is valid (YYYY-MM)
    """
    # Check if WO number already exists
    statement = select(WorkOrder).where(WorkOrder.wo_number == work_order_data.wo_number)
    existing = session.exec(statement).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Work order '{work_order_data.wo_number}' already exists"
        )
    
    # Verify machine exists
    machine = session.get(Machine, work_order_data.machine_id)
    if not machine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Machine with ID {work_order_data.machine_id} not found"
        )
    
    # Create work order
    payload = work_order_data.model_dump()
    work_order = WorkOrder(**payload, created_by=current_user.id)
    session.add(work_order)
    session.commit()
    session.refresh(work_order)
    return work_order


@router.patch("/{work_order_id}", response_model=WorkOrderRead)
def update_work_order(
    work_order_id: int,
    work_order_data: WorkOrderUpdate,
    session: Session = Depends(get_session),
    current_user: Employee = Depends(require_roles(["SUPERVISOR"])),
):
    """Update a work order (Supervisor only)."""
    work_order = session.get(WorkOrder, work_order_id)
    if not work_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work order not found"
        )
    
    # Check WO number uniqueness if being updated
    if work_order_data.wo_number and work_order_data.wo_number != work_order.wo_number:
        statement = select(WorkOrder).where(WorkOrder.wo_number == work_order_data.wo_number)
        existing = session.exec(statement).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Work order '{work_order_data.wo_number}' already exists"
            )
    
    # Verify machine exists if being updated
    if work_order_data.machine_id:
        machine = session.get(Machine, work_order_data.machine_id)
        if not machine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Machine with ID {work_order_data.machine_id} not found"
            )
    
    # Update fields
    update_data = work_order_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(work_order, key, value)
    
    session.add(work_order)
    session.commit()
    session.refresh(work_order)
    return work_order


@router.delete("/{work_order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_work_order(
    work_order_id: int,
    session: Session = Depends(get_session),
    current_user: Employee = Depends(require_roles(["SUPERVISOR"])),
):
    """Delete a work order (Supervisor only)."""
    work_order = session.get(WorkOrder, work_order_id)
    if not work_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work order not found"
        )

    # Check for dependencies before deletion
    from sqlmodel import select
    from app.models.models import JobCard

    # Check if work order is used in job cards
    jc_stmt = select(JobCard).where(JobCard.work_order_id == work_order_id)
    job_cards = session.exec(jc_stmt).first()
    if job_cards:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete work order '{work_order.wo_number}' - it is referenced by job cards. Remove associated job cards first."
        )

    session.delete(work_order)
    session.commit()
    return None
