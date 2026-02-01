from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from passlib.context import CryptContext
from app.database import get_session
from app.models.employee import Employee
from app.schemas.employee import EmployeeCreate, EmployeeRead, EmployeeUpdate
from datetime import datetime

router = APIRouter(prefix="/employees", tags=["employees"])

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.get("/", response_model=List[EmployeeRead])
def get_employees(
    skip: int = 0,
    limit: int = 100,
    role: str = None,
    team: str = None,
    session: Session = Depends(get_session)
):
    """Get all employees with optional filters."""
    statement = select(Employee)
    
    if role:
        statement = statement.where(Employee.role == role)
    if team:
        statement = statement.where(Employee.team == team)
    
    statement = statement.offset(skip).limit(limit)
    employees = session.exec(statement).all()
    return employees


@router.get("/{employee_id}", response_model=EmployeeRead)
def get_employee(
    employee_id: int,
    session: Session = Depends(get_session)
):
    """Get a single employee by ID."""
    employee = session.get(Employee, employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    return employee


@router.post("/", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
def create_employee(
    employee_data: EmployeeCreate,
    session: Session = Depends(get_session)
):
    """Create a new employee."""
    # Check if employee with ec_number already exists
    statement = select(Employee).where(Employee.ec_number == employee_data.ec_number)
    existing_employee = session.exec(statement).first()
    if existing_employee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee with this EC number already exists"
        )
    
    # Hash password
    hashed_password = pwd_context.hash(employee_data.password)
    
    # Create employee
    employee_dict = employee_data.model_dump(exclude={"password"})
    employee = Employee(**employee_dict, hashed_password=hashed_password)
    
    session.add(employee)
    session.commit()
    session.refresh(employee)
    return employee


@router.patch("/{employee_id}", response_model=EmployeeRead)
def update_employee(
    employee_id: int,
    employee_data: EmployeeUpdate,
    session: Session = Depends(get_session)
):
    """Update an employee."""
    employee = session.get(Employee, employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Update fields
    update_data = employee_data.model_dump(exclude_unset=True)
    
    # Hash password if being updated
    if "password" in update_data:
        hashed_password = pwd_context.hash(update_data.pop("password"))
        setattr(employee, "hashed_password", hashed_password)
    
    for key, value in update_data.items():
        setattr(employee, key, value)
    
    employee.updated_at = datetime.utcnow()
    session.add(employee)
    session.commit()
    session.refresh(employee)
    return employee


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(
    employee_id: int,
    session: Session = Depends(get_session)
):
    """Delete an employee."""
    employee = session.get(Employee, employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    session.delete(employee)
    session.commit()
    return None
