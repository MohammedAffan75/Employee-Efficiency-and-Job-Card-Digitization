from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.security import get_current_active_user, require_roles
from app.models.models import EfficiencyEmployee
from app.models.employee import Employee
from app.schemas.employee import EmployeeCreate, EmployeeRead, EmployeeUpdate

router = APIRouter()


@router.get("/", response_model=List[EmployeeRead])
def get_employees(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: EfficiencyEmployee = Depends(require_roles(["ADMIN", "SUPERVISOR"])),
):
    """Get all employees. Only accessible by ADMIN and SUPERVISOR roles.
    Supervisors can only see operators they created and cannot see other supervisors or admins."""
    if current_user.role == "SUPERVISOR":
        # Supervisors can only see operators they created
        statement = (select(Employee)
                   .where(
                       (Employee.created_by == current_user.id) &  # Created by current supervisor
                       (Employee.role == "OPERATOR")  # Only operators
                   )
                   .offset(skip)
                   .limit(limit))
    else:
        # Admins can see all employees
        statement = select(Employee).offset(skip).limit(limit)
    
    employees = session.exec(statement).all()
    return employees


@router.get("/{employee_id}", response_model=EmployeeRead)
def get_employee(
    employee_id: int,
    session: Session = Depends(get_session),
    current_user: EfficiencyEmployee = Depends(require_roles(["ADMIN", "SUPERVISOR"])),
):
    """Get a single employee by ID. Only accessible by ADMIN and SUPERVISOR roles."""
    employee = session.get(Employee, employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found"
        )

    if current_user.role == "SUPERVISOR":
        if employee.role != "OPERATOR":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Supervisors can only delete operator accounts",
            )
        if employee.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete operators you created",
            )
    return employee


@router.post("/", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
def create_employee(
    employee_data: EmployeeCreate,
    session: Session = Depends(get_session),
    current_user: EfficiencyEmployee = Depends(require_roles(["SUPERVISOR", "ADMIN"])),
):
    """Create a new employee. Accessible by ADMIN and SUPERVISOR roles."""
    # Check if employee with ec_number already exists
    statement = select(Employee).where(Employee.ec_number == employee_data.ec_number)
    existing_employee = session.exec(statement).first()
    if existing_employee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee with this EC number already exists",
        )

    # Supervisors can only create operator accounts
    if current_user.role == "SUPERVISOR" and employee_data.role != "OPERATOR":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Supervisors can only create operator accounts",
        )

    # Require efficiency module for supervisors created by admin
    if employee_data.role == "SUPERVISOR" and not employee_data.supervisor_efficiency_module:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Supervisor efficiency module is required",
        )

    # Hash password
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed_password = pwd_context.hash(employee_data.password)
    
    # Create employee
    employee_dict = employee_data.model_dump(exclude={"password"})
    if employee_data.role != "SUPERVISOR":
        employee_dict["supervisor_efficiency_module"] = None
    employee = Employee(**employee_dict, hashed_password=hashed_password, created_by=current_user.id)
    
    session.add(employee)
    session.commit()
    session.refresh(employee)
    return employee


@router.patch("/{employee_id}", response_model=EmployeeRead)
def update_employee(
    employee_id: int,
    employee_data: EmployeeUpdate,
    session: Session = Depends(get_session),
    current_user: EfficiencyEmployee = Depends(require_roles(["SUPERVISOR"])),
):
    """Update an employee. Accessible by SUPERVISOR role."""
    employee = session.get(Employee, employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found"
        )

    # Update fields
    update_data = employee_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(employee, key, value)

    employee.updated_at = datetime.utcnow()
    session.add(employee)
    session.commit()
    session.refresh(employee)
    return employee


@router.patch("/{employee_id}/status", response_model=EmployeeRead)
def toggle_employee_status(
    employee_id: int,
    session: Session = Depends(get_session),
    current_user: EfficiencyEmployee = Depends(require_roles(["SUPERVISOR"])),
):
    """Activate or deactivate an employee. Accessible by SUPERVISOR role."""
    employee = session.get(Employee, employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found"
        )

    # Prevent self-deactivation
    if employee_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own account"
        )

    # Toggle active status
    employee.is_active = not employee.is_active
    employee.updated_at = datetime.utcnow()
    session.add(employee)
    session.commit()
    session.refresh(employee)
    return employee


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(
    employee_id: int,
    session: Session = Depends(get_session),
    current_user: EfficiencyEmployee = Depends(require_roles(["SUPERVISOR", "ADMIN"])),
):
    """Delete an employee permanently. Accessible by SUPERVISOR and ADMIN roles. Use with caution."""
    employee = session.get(Employee, employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found"
        )

    # Check for dependencies before deletion
    from sqlmodel import select
    from app.models.models import JobCard, ValidationFlag, EfficiencyPeriod, AuditLog

    # Check if employee has job cards
    job_card_stmt = select(JobCard).where(
        (JobCard.employee_id == employee_id) |
        (JobCard.supervisor_id == employee_id) |
        (JobCard.approved_by == employee_id)
    )
    job_cards = session.exec(job_card_stmt).first()
    if job_cards:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete employee with associated job cards. Deactivate instead."
        )

    # Check if employee has validation flags
    flag_stmt = select(ValidationFlag).where(ValidationFlag.resolved_by == employee_id)
    flags = session.exec(flag_stmt).first()
    if flags:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete employee with associated validation flags. Deactivate instead."
        )

    # Check if employee has efficiency periods
    period_stmt = select(EfficiencyPeriod).where(EfficiencyPeriod.employee_id == employee_id)
    periods = session.exec(period_stmt).first()
    if periods:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete employee with associated efficiency records. Deactivate instead."
        )

    # Check if employee has audit logs
    audit_stmt = select(AuditLog).where(AuditLog.performed_by == employee_id)
    audits = session.exec(audit_stmt).first()
    if audits:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete employee with associated audit logs. Deactivate instead."
        )

    session.delete(employee)
    session.commit()
    return None
