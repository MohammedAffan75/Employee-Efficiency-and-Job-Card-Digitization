"""
Authentication routes for employee login and user info.
Uses EC number and password for authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.config import settings
from app.core.database import get_session
from app.core.security import (
    authenticate_employee,
    create_access_token,
    get_current_user,
)
from app.models.employee import Employee
from app.schemas.auth_schemas import AuthIn, TokenOut, EmployeeInfo

router = APIRouter()


@router.post("/login", response_model=TokenOut)
def login(credentials: AuthIn, session: Session = Depends(get_session)):
    """
    Employee login endpoint.
    
    Authenticates employee using EC number and password.
    Returns JWT token with employee_id, ec_number, and role in payload.
    """
    # Authenticate employee
    employee = authenticate_employee(session, credentials.ec_number, credentials.password)
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect EC number or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create JWT token with employee info
    supervisor_module = getattr(employee, "supervisor_efficiency_module", None)
    if supervisor_module is None and employee.role.value == "OPERATOR" and employee.created_by:
        creator = session.get(Employee, employee.created_by)
        if creator is not None:
            supervisor_module = getattr(creator, "supervisor_efficiency_module", None)

    access_token = create_access_token(
        data={
            "sub": str(employee.id),  # Employee ID as subject
            "ec": employee.ec_number,  # EC number
            "role": employee.role.value,  # Role (ADMIN, SUPERVISOR, OPERATOR)
            "supervisor_efficiency_module": (
                supervisor_module.value
                if supervisor_module is not None
                else None
            ),
        },
        expires_minutes=settings.access_token_expire_minutes
    )
    
    return TokenOut(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,  # Convert to seconds
        employee=EmployeeInfo(
            id=employee.id,
            ec_number=employee.ec_number,
            name=employee.name,
            role=employee.role.value,
            is_active=employee.is_active,
            supervisor_efficiency_module=(
                supervisor_module.value
                if supervisor_module is not None
                else None
            ),
        )
    )


@router.get("/me", response_model=EmployeeInfo)
def get_me(
    current_user: Employee = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Get current employee information from JWT token.
    
    Requires valid JWT token in Authorization header.
    Returns employee details without sensitive information.
    """
    supervisor_module = getattr(current_user, "supervisor_efficiency_module", None)
    if supervisor_module is None and current_user.role.value == "OPERATOR" and current_user.created_by:
        creator = session.get(Employee, current_user.created_by)
        if creator is not None:
            supervisor_module = getattr(creator, "supervisor_efficiency_module", None)

    return EmployeeInfo(
        id=current_user.id,
        ec_number=current_user.ec_number,
        name=current_user.name,
        role=current_user.role.value,
        is_active=current_user.is_active,
        supervisor_efficiency_module=(
            supervisor_module.value
            if supervisor_module is not None
            else None
        ),
    )
