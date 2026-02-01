"""
Machines CRUD routes (Admin only).
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.security import require_roles
from app.models.models import Machine
from app.models.employee import Employee
from app.schemas.machine_schemas import (
    MachineCreate,
    MachineRead,
    MachineUpdate,
)

router = APIRouter()


@router.get("/", response_model=List[MachineRead])
def list_machines(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: Employee = Depends(require_roles(["ADMIN", "SUPERVISOR", "OPERATOR"])),
):
    """
    List all machines (All roles).
    
    Supervisors: only see machines they created.
    Supports pagination with skip and limit parameters.
    """
    statement = select(Machine)
    if current_user.role == "SUPERVISOR":
        statement = statement.where(Machine.created_by == current_user.id)
    statement = statement.offset(skip).limit(limit)
    machines = session.exec(statement).all()
    return machines


@router.get("/{machine_id}", response_model=MachineRead)
def get_machine(
    machine_id: int,
    session: Session = Depends(get_session),
    current_user: Employee = Depends(require_roles(["ADMIN", "SUPERVISOR", "OPERATOR"])),
):
    """Get a single machine by ID (All roles)."""
    machine = session.get(Machine, machine_id)
    if not machine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Machine not found"
        )
    return machine


@router.post("/", response_model=MachineRead, status_code=status.HTTP_201_CREATED)
def create_machine(
    machine_data: MachineCreate,
    session: Session = Depends(get_session),
    current_user: Employee = Depends(require_roles(["SUPERVISOR"])),
):
    """
    Create a new machine (Supervisor only).
    
    Validates that machine code is unique.
    """
    # Check if machine code already exists
    statement = select(Machine).where(Machine.machine_code == machine_data.machine_code)
    existing = session.exec(statement).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Machine code '{machine_data.machine_code}' already exists"
        )
    
    # Create machine
    payload = machine_data.model_dump()
    machine = Machine(**payload, created_by=current_user.id)
    session.add(machine)
    session.commit()
    session.refresh(machine)
    return machine


@router.patch("/{machine_id}", response_model=MachineRead)
def update_machine(
    machine_id: int,
    machine_data: MachineUpdate,
    session: Session = Depends(get_session),
    current_user: Employee = Depends(require_roles(["SUPERVISOR"])),
):
    """Update a machine (Supervisor only)."""
    machine = session.get(Machine, machine_id)
    if not machine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Machine not found"
        )
    
    # Check machine code uniqueness if being updated
    if machine_data.machine_code and machine_data.machine_code != machine.machine_code:
        statement = select(Machine).where(Machine.machine_code == machine_data.machine_code)
        existing = session.exec(statement).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Machine code '{machine_data.machine_code}' already exists"
            )
    
    # Update fields
    update_data = machine_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(machine, key, value)
    
    session.add(machine)
    session.commit()
    session.refresh(machine)
    return machine


@router.delete("/{machine_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_machine(
    machine_id: int,
    session: Session = Depends(get_session),
    current_user: Employee = Depends(require_roles(["SUPERVISOR"])),
):
    """Delete a machine (Supervisor only)."""
    machine = session.get(Machine, machine_id)
    if not machine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Machine not found"
        )

    # Check for dependencies before deletion
    from sqlmodel import select
    from app.models.models import WorkOrder

    # Check if machine is used in work orders
    wo_stmt = select(WorkOrder).where(WorkOrder.machine_id == machine_id)
    work_orders = session.exec(wo_stmt).first()
    if work_orders:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete machine '{machine.machine_code}' - it is referenced by work orders. Remove associated work orders first."
        )

    session.delete(machine)
    session.commit()
    return None
