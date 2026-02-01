"""
Admin dashboard endpoints for system-wide analytics and management.
"""

from datetime import date, datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, and_

from app.core.database import get_async_session
from app.core.security import require_roles
from app.models.employee import Employee, RoleEnum
from app.models.models import (
    Machine,
    ActivityCode,
    JobCard,
    ValidationFlag,
    EfficiencyPeriod,
)

router = APIRouter()


# ============================================================================
# GET /dashboard/stats - System Statistics
# ============================================================================

@router.get("/dashboard/stats")
async def get_system_stats(
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(require_roles(["ADMIN"])),
):
    """
    Get system-wide statistics.
    
    Returns:
    - total_employees: Total employee count
    - active_employees: Active employee count
    - total_machines: Total machine count
    - total_activity_codes: Total activity code count
    - total_job_cards_month: Job cards created this month
    - total_validations_unresolved: Unresolved validation flags
    """
    # Total and active employees
    total_emp_stmt = select(func.count(Employee.id))
    total_emp_result = await session.execute(total_emp_stmt)
    total_employees = total_emp_result.scalar() or 0
    
    active_emp_stmt = select(func.count(Employee.id)).where(Employee.is_active == True)
    active_emp_result = await session.execute(active_emp_stmt)
    active_employees = active_emp_result.scalar() or 0
    
    # Total machines
    machine_stmt = select(func.count(Machine.id))
    machine_result = await session.execute(machine_stmt)
    total_machines = machine_result.scalar() or 0
    
    # Total activity codes
    activity_stmt = select(func.count(ActivityCode.id))
    activity_result = await session.execute(activity_stmt)
    total_activity_codes = activity_result.scalar() or 0
    
    # Job cards this month
    today = date.today()
    month_start = date(today.year, today.month, 1)
    jobcard_stmt = select(func.count(JobCard.id)).where(
        JobCard.entry_date >= month_start
    )
    jobcard_result = await session.execute(jobcard_stmt)
    total_job_cards_month = jobcard_result.scalar() or 0
    
    # Unresolved validations
    validation_stmt = select(func.count(ValidationFlag.id)).where(
        ValidationFlag.resolved == False
    )
    validation_result = await session.execute(validation_stmt)
    total_validations_unresolved = validation_result.scalar() or 0
    
    return {
        "total_employees": total_employees,
        "active_employees": active_employees,
        "total_machines": total_machines,
        "total_activity_codes": total_activity_codes,
        "total_job_cards_month": total_job_cards_month,
        "total_validations_unresolved": total_validations_unresolved,
    }


# ============================================================================
# GET /dashboard/role-distribution - Employee Distribution by Role
# ============================================================================

@router.get("/dashboard/role-distribution")
async def get_role_distribution(
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(require_roles(["ADMIN"])),
):
    """
    Get employee count by role.
    
    Returns: List of {role: str, count: int}
    """
    stmt = (
        select(
            Employee.role,
            func.count(Employee.id).label('count')
        )
        .where(Employee.is_active == True)
        .group_by(Employee.role)
    )
    
    result = await session.execute(stmt)
    rows = result.all()
    
    return [
        {"role": row.role, "count": row.count}
        for row in rows
    ]


# ============================================================================
# GET /dashboard/department-summary - Department Summary (All Employees)
# ============================================================================

@router.get("/dashboard/department-summary")
async def get_department_summary(
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(require_roles(["ADMIN"])),
):
    """
    Get overall department performance metrics for the current month.
    
    Returns: {
        total_employees: int,
        avg_time_efficiency: float,
        avg_qty_efficiency: float,
        avg_task_efficiency: float,
        total_hours: float,
        total_job_cards: int,
        avg_awc_pct: float
    }
    """
    # Get current month date range
    today = date.today()
    month_start = date(today.year, today.month, 1)
    
    # Get all active employees
    emp_stmt = select(Employee.id).where(Employee.is_active == True)
    emp_result = await session.execute(emp_stmt)
    employee_ids = [row[0] for row in emp_result.all()]
    
    if not employee_ids:
        return {
            "total_employees": 0,
            "avg_time_efficiency": 0,
            "avg_qty_efficiency": 0,
            "avg_task_efficiency": 0,
            "total_hours": 0,
            "total_job_cards": 0,
            "avg_awc_pct": 0,
        }
    
    # Get efficiency periods for this month
    eff_stmt = select(EfficiencyPeriod).where(
        EfficiencyPeriod.employee_id.in_(employee_ids),
        EfficiencyPeriod.period_start >= month_start,
    )
    eff_result = await session.execute(eff_stmt)
    periods = eff_result.scalars().all()
    
    # Get job cards count for this month
    jc_stmt = select(func.count(JobCard.id)).where(
        JobCard.employee_id.in_(employee_ids),
        JobCard.entry_date >= month_start,
    )
    jc_result = await session.execute(jc_stmt)
    job_card_count = jc_result.scalar() or 0
    
    # Calculate metrics
    if periods:
        avg_time_eff = sum(p.time_efficiency or 0 for p in periods) / len(periods)
        avg_qty_eff = sum(p.quantity_efficiency or 0 for p in periods) / len(periods)
        avg_task_eff = sum(p.task_efficiency or 0 for p in periods) / len(periods)
        total_hours = sum(p.actual_hours or 0 for p in periods)
        avg_awc = sum(p.awc_pct or 0 for p in periods) / len(periods)
    else:
        avg_time_eff = avg_qty_eff = avg_task_eff = total_hours = avg_awc = 0
    
    return {
        "total_employees": len(employee_ids),
        "avg_time_efficiency": round(avg_time_eff, 2),
        "avg_qty_efficiency": round(avg_qty_eff, 2),
        "avg_task_efficiency": round(avg_task_eff, 2),
        "total_hours": round(total_hours, 2),
        "total_job_cards": job_card_count,
        "avg_awc_pct": round(avg_awc * 100, 2),
    }


# ============================================================================
# GET /dashboard/employee-performance - Individual Employee Performance
# ============================================================================

@router.get("/dashboard/employee-performance")
async def get_employee_performance(
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(require_roles(["ADMIN"])),
):
    """
    Get individual employee performance metrics for the current month.
    Excludes ADMIN and SUPERVISOR roles.

    Returns: List of employee performance metrics
    """
    # Get current month date range
    today = date.today()
    month_start = date(today.year, today.month, 1)

    # Get active operators (exclude admin and supervisor)
    emp_stmt = select(Employee).where(
        Employee.is_active == True,
        Employee.role != RoleEnum.ADMIN,
        Employee.role != RoleEnum.SUPERVISOR,
    )
    emp_result = await session.execute(emp_stmt)
    employees = emp_result.scalars().all()

    if not employees:
        return []

    employee_metrics = []

    for emp in employees:
        # Get efficiency periods for this employee this month
        eff_stmt = select(EfficiencyPeriod).where(
            EfficiencyPeriod.employee_id == emp.id,
            EfficiencyPeriod.period_start >= month_start,
        )
        eff_result = await session.execute(eff_stmt)
        periods = eff_result.scalars().all()

        # Calculate averages for this employee
        if periods:
            avg_time_eff = sum(p.time_efficiency or 0 for p in periods) / len(periods)
            avg_qty_eff = sum(p.quantity_efficiency or 0 for p in periods) / len(periods)
            avg_task_eff = sum(p.task_efficiency or 0 for p in periods) / len(periods)
            total_hours = sum(p.actual_hours or 0 for p in periods)
        else:
            avg_time_eff = avg_qty_eff = avg_task_eff = total_hours = 0

        employee_metrics.append({
            "employee_id": emp.id,
            "employee_name": emp.name,
            "ec_number": emp.ec_number,
            "time_efficiency": round(avg_time_eff, 2),
            "quantity_efficiency": round(avg_qty_eff, 2),
            "task_efficiency": round(avg_task_eff, 2),
            "total_hours": round(total_hours, 2),
        })

    return employee_metrics
