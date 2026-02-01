"""
Reporting endpoints for dashboard and data exports.
"""

import io
import csv
from typing import Optional
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_async_session
from app.core.security import require_roles
from app.models.models import (
    EfficiencyPeriod,
    JobCard,
    ActivityCode,
)
from app.models.employee import Employee, RoleEnum
from app.schemas.reporting_schemas import DashboardSummary
from app.services.efficiency_engine import compute_employee_efficiency
from sqlalchemy import func, and_

router = APIRouter()


# ============================================================================
# GET /dashboard/summary - Team Dashboard KPIs
# ============================================================================

@router.get("/dashboard/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    start: date = Query(..., description="Period start date (YYYY-MM-DD)"),
    end: date = Query(..., description="Period end date (YYYY-MM-DD)"),
    force: bool = Query(False, description="Force recompute efficiency for all employees"),
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(require_roles(["SUPERVISOR", "ADMIN"])),
) -> DashboardSummary:
    """
    Get aggregated KPIs for all employees.
    
    Returns:
    - avg_time_efficiency: Average time efficiency across all employees
    - avg_qty_efficiency: Average quantity efficiency
    - avg_task_efficiency: Average task efficiency
    - avg_awc_pct: Average AWC percentage
    - total_std_hours: Sum of standard hours allowed
    - total_actual_hours: Sum of actual productive hours
    
    Access: SUPERVISOR or ADMIN only
    """
    # Build query for efficiency periods - get all active employees
    emp_stmt = select(Employee.id).where(
        Employee.is_active == True,
        Employee.role == RoleEnum.OPERATOR,
    )
    emp_result = await session.execute(emp_stmt)
    employee_ids = [row[0] for row in emp_result.all()]
    
    stmt = select(EfficiencyPeriod).where(
        EfficiencyPeriod.period_start >= start,
        EfficiencyPeriod.period_end <= end,
    )
    
    if employee_ids:
        stmt = stmt.where(EfficiencyPeriod.employee_id.in_(employee_ids))
    
    # Fetch efficiency periods
    result = await session.execute(stmt)
    periods = result.scalars().all()
    
    # If force=true or no precomputed data, compute on-demand for all active employees, then refetch
    if force or not periods:
        for emp_id in employee_ids:
            await compute_employee_efficiency(emp_id, start, end, session)
        result = await session.execute(stmt)
        periods = result.scalars().all()
        
        if not periods:
            # Still no data: return zeros
            return DashboardSummary(
                team_id=None,
                period_start=start.isoformat(),
                period_end=end.isoformat(),
                employee_count=0,
                avg_time_efficiency=0.0,
                avg_qty_efficiency=0.0,
                avg_task_efficiency=0.0,
                avg_awc_pct=0.0,
                total_std_hours=0.0,
                total_actual_hours=0.0,
            )
    
    # Aggregate KPIs
    n = len(periods)
    avg_time_eff = sum(p.time_efficiency or 0.0 for p in periods) / n
    avg_qty_eff = sum(p.quantity_efficiency or 0.0 for p in periods) / n
    avg_task_eff = sum(p.task_efficiency or 0.0 for p in periods) / n
    avg_awc = sum(p.awc_pct or 0.0 for p in periods) / n
    total_std = sum(p.standard_hours_allowed or 0.0 for p in periods)
    total_actual = sum(p.actual_hours or 0.0 for p in periods)
    
    # Count unique employees
    unique_employees = len(set(p.employee_id for p in periods))
    
    return DashboardSummary(
        team_id=None,
        period_start=start.isoformat(),
        period_end=end.isoformat(),
        employee_count=unique_employees,
        avg_time_efficiency=round(avg_time_eff, 2),
        avg_qty_efficiency=round(avg_qty_eff, 2),
        avg_task_efficiency=round(avg_task_eff, 2),
        avg_awc_pct=round(avg_awc, 4),
        total_std_hours=round(total_std, 2),
        total_actual_hours=round(total_actual, 2),
    )


# ============================================================================
# GET /report/monthly - Monthly CSV Export
# ============================================================================

@router.get("/report/monthly")
async def get_monthly_report(
    month: str = Query(..., description="Month in YYYY-MM format", regex=r"^\d{4}-\d{2}$"),
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(require_roles(["SUPERVISOR", "ADMIN"])),
):
    """
    Generate monthly efficiency report as CSV.
    
    Columns:
    - employee_id
    - ec_number
    - name
    - team
    - total_hours
    - std_hours_allowed
    - time_efficiency
    - qty_efficiency
    - task_efficiency
    - awc_pct
    
    Returns: Streaming CSV file
    Access: SUPERVISOR or ADMIN only
    """
    # Parse month
    try:
        year, month_num = month.split('-')
        period_start = date(int(year), int(month_num), 1)
        # Last day of month
        if int(month_num) == 12:
            period_end = date(int(year) + 1, 1, 1) - relativedelta(days=1)
        else:
            period_end = date(int(year), int(month_num) + 1, 1) - relativedelta(days=1)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid month format. Use YYYY-MM"
        )
    
    # Fetch efficiency periods for the month
    stmt = (
        select(EfficiencyPeriod, Employee)
        .join(Employee, EfficiencyPeriod.employee_id == Employee.id)
        .where(
            EfficiencyPeriod.period_start >= period_start,
            EfficiencyPeriod.period_end <= period_end,
        )
        .order_by(Employee.team, Employee.name)
    )
    
    result = await session.execute(stmt)
    rows = result.all()
    
    # Generate CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'employee_id',
        'ec_number',
        'name',
        'team',
        'total_hours',
        'std_hours_allowed',
        'time_efficiency',
        'qty_efficiency',
        'task_efficiency',
        'awc_pct'
    ])
    
    # Write data rows
    for period, employee in rows:
        writer.writerow([
            employee.id,
            employee.ec_number,
            employee.name,
            employee.team or '',
            round(period.actual_hours or 0.0, 2),
            round(period.standard_hours_allowed or 0.0, 2),
            round(period.time_efficiency or 0.0, 2),
            round(period.quantity_efficiency or 0.0, 2),
            round(period.task_efficiency or 0.0, 2),
            round(period.awc_pct or 0.0, 4),
        ])
    
    # Prepare response
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=efficiency_report_{month}.csv"
        }
    )


# ============================================================================
# GET /report/employee-details - Detailed Employee Report (Bonus)
# ============================================================================

@router.get("/report/employee-details")
async def get_employee_details_report(
    employee_id: int = Query(..., description="Employee ID"),
    start: date = Query(..., description="Period start date"),
    end: date = Query(..., description="Period end date"),
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(require_roles(["SUPERVISOR", "ADMIN"])),
):
    """
    Generate detailed employee report as CSV with jobcard-level data.
    
    Columns include jobcard details, activity codes, hours, quantities, etc.
    
    Returns: Streaming CSV file
    Access: SUPERVISOR or ADMIN only
    """
    # Fetch employee
    employee = await session.get(Employee, employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee {employee_id} not found"
        )
    
    # Fetch jobcards with activity details
    stmt = (
        select(JobCard, ActivityCode)
        .outerjoin(ActivityCode, JobCard.activity_code_id == ActivityCode.id)
        .where(
            JobCard.employee_id == employee_id,
            JobCard.entry_date >= start,
            JobCard.entry_date <= end,
        )
        .order_by(JobCard.entry_date)
    )
    
    result = await session.execute(stmt)
    rows = result.all()
    
    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'jobcard_id',
        'entry_date',
        'work_order_id',
        'activity_code',
        'activity_desc',
        'qty',
        'actual_hours',
        'std_hours_per_unit',
        'std_hours_allowed',
        'status',
        'source'
    ])
    
    # Data rows
    for jc, activity in rows:
        std_per_unit = activity.std_hours_per_unit if activity else 0.0
        std_allowed = (std_per_unit or 0.0) * (jc.qty or 0.0)
        
        writer.writerow([
            jc.id,
            jc.entry_date.isoformat(),
            jc.work_order_id,
            activity.code if activity else 'N/A',
            jc.activity_desc,
            round(jc.qty or 0.0, 2),
            round(jc.actual_hours or 0.0, 2),
            round(std_per_unit or 0.0, 4),
            round(std_allowed, 2),
            jc.status.value,
            jc.source.value,
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=employee_{employee_id}_detail_{start}_{end}.csv"
        }
    )


# ============================================================================
# GET /activity-distribution - Activity Distribution by Type
# ============================================================================

@router.get("/activity-distribution")
async def get_activity_distribution(
    employee_id: int = Query(..., description="Employee ID"),
    start: date = Query(..., description="Period start date"),
    end: date = Query(..., description="Period end date"),
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(require_roles(["OPERATOR", "SUPERVISOR", "ADMIN"])),
):
    """
    Get distribution of activities by activity code for an employee.
    
    Returns: List of {activity_type: str, count: int, hours: float}
    """
    # Query job cards with activity codes
    stmt = (
        select(
            ActivityCode.code,
            func.count(JobCard.id).label('job_count'),
            func.sum(JobCard.actual_hours).label('total_hours')
        )
        .join(JobCard, ActivityCode.id == JobCard.activity_code_id)
        .where(
            JobCard.employee_id == employee_id,
            JobCard.entry_date >= start,
            JobCard.entry_date <= end,
        )
        .group_by(ActivityCode.code)
    )
    
    result = await session.execute(stmt)
    rows = result.all()
    
    # Format for frontend
    distribution = [
        {
            "activity_type": row.code or "AWC",
            "count": int(row.job_count or 0),
            "hours": float(row.total_hours or 0)
        }
        for row in rows
    ]
    
    # Add AWC activities (no activity code)
    awc_count_stmt = select(func.count(JobCard.id)).where(
        JobCard.employee_id == employee_id,
        JobCard.entry_date >= start,
        JobCard.entry_date <= end,
        JobCard.activity_code_id == None,
    )
    awc_count_result = await session.execute(awc_count_stmt)
    awc_count = awc_count_result.scalar() or 0
    
    awc_hours_stmt = select(func.sum(JobCard.actual_hours)).where(
        JobCard.employee_id == employee_id,
        JobCard.entry_date >= start,
        JobCard.entry_date <= end,
        JobCard.activity_code_id == None,
    )
    awc_hours_result = await session.execute(awc_hours_stmt)
    awc_hours = awc_hours_result.scalar() or 0
    
    if awc_count > 0:
        distribution.append({
            "activity_type": "AWC",
            "count": int(awc_count),
            "hours": float(awc_hours)
        })
    
    return distribution


# ============================================================================
# GET /monthly-trend - Monthly Trend for Employee
# ============================================================================

@router.get("/monthly-trend")
async def get_monthly_trend(
    employee_id: int = Query(..., description="Employee ID"),
    start: date = Query(..., description="Period start date"),
    end: date = Query(..., description="Period end date"),
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(require_roles(["OPERATOR", "SUPERVISOR", "ADMIN"])),
):
    """
    Get monthly efficiency trend for an employee.
    
    Returns: List of {month: str, time_eff: float, qty_eff: float, task_eff: float}
    """
    stmt = (
        select(EfficiencyPeriod)
        .where(
            EfficiencyPeriod.employee_id == employee_id,
            EfficiencyPeriod.period_start >= start,
            EfficiencyPeriod.period_end <= end,
        )
        .order_by(EfficiencyPeriod.period_start)
    )
    
    result = await session.execute(stmt)
    periods = result.scalars().all()
    
    # Group by month
    monthly_data = {}
    for period in periods:
        month_key = period.period_start.strftime('%Y-%m')
        if month_key not in monthly_data:
            monthly_data[month_key] = {
                'time_eff': [],
                'qty_eff': [],
                'task_eff': []
            }
        
        monthly_data[month_key]['time_eff'].append(period.time_efficiency or 0)
        monthly_data[month_key]['qty_eff'].append(period.quantity_efficiency or 0)
        monthly_data[month_key]['task_eff'].append(period.task_efficiency or 0)
    
    # Calculate averages
    trend = []
    for month, data in sorted(monthly_data.items()):
        trend.append({
            "month": month,
            "time_efficiency": round(sum(data['time_eff']) / len(data['time_eff']), 2) if data['time_eff'] else 0,
            "quantity_efficiency": round(sum(data['qty_eff']) / len(data['qty_eff']), 2) if data['qty_eff'] else 0,
            "task_efficiency": round(sum(data['task_eff']) / len(data['task_eff']), 2) if data['task_eff'] else 0,
        })
    
    return trend


# ============================================================================
# GET /team-efficiency - Team Efficiency Metrics
# ============================================================================

@router.get("/all-employees-efficiency")
async def get_all_employees_efficiency(
    start: date = Query(..., description="Period start date"),
    end: date = Query(..., description="Period end date"),
    force: bool = Query(False, description="Force recompute efficiency for all employees"),
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(require_roles(["SUPERVISOR", "ADMIN"])),
):
    """
    Get individual employee efficiency metrics for all active employees.
    
    For supervisors, only shows employees who have job cards created by them.
    For admins, shows all active operators.
    
    Returns: List of employee efficiency metrics
    """
    # Get all active employees
    emp_stmt = select(Employee).where(
        Employee.is_active == True,
        Employee.role == RoleEnum.OPERATOR,
    )
    emp_result = await session.execute(emp_stmt)
    employees = emp_result.scalars().all()
    
    # For supervisors, filter to only show employees they created
    if current_user.role == RoleEnum.SUPERVISOR:
        # Filter employees to only those created by this supervisor
        employees = [emp for emp in employees if emp.created_by == current_user.id]
    
    if not employees:
        return []
    
    employee_metrics = []
    
    for emp in employees:
        # Get efficiency periods for this employee
        eff_stmt = select(EfficiencyPeriod).where(
            EfficiencyPeriod.employee_id == emp.id,
            EfficiencyPeriod.period_start >= start,
            EfficiencyPeriod.period_end <= end,
        )
        eff_result = await session.execute(eff_stmt)
        periods = eff_result.scalars().all()
        
        # If force=true or missing, compute on-demand for this employee and refetch
        if force or not periods:
            await compute_employee_efficiency(emp.id, start, end, session)
            eff_result = await session.execute(eff_stmt)
            periods = eff_result.scalars().all()

        # Calculate averages for this employee
        if periods:
            avg_time_eff = sum(p.time_efficiency or 0 for p in periods) / len(periods)
            avg_qty_eff = sum(p.quantity_efficiency or 0 for p in periods) / len(periods)
            avg_task_eff = sum(p.task_efficiency or 0 for p in periods) / len(periods)
            avg_awc = sum(p.awc_pct or 0 for p in periods) / len(periods)
            std_hours = sum(p.standard_hours_allowed or 0 for p in periods)
            actual_hours = sum(p.actual_hours or 0 for p in periods)
        else:
            avg_time_eff = avg_qty_eff = avg_task_eff = avg_awc = std_hours = actual_hours = 0
        
        employee_metrics.append({
            "employee_id": emp.id,
            "employee_name": emp.name,
            "ec_number": emp.ec_number,
            "time_efficiency": round(avg_time_eff, 2),
            "quantity_efficiency": round(avg_qty_eff, 2),
            "task_efficiency": round(avg_task_eff, 2),
            "awc_pct": round(avg_awc, 4),
            "standard_hours_allowed": round(std_hours, 2),
            "actual_hours": round(actual_hours, 2),
        })
    
    return employee_metrics


# ============================================================================
# GET /all-trend - All Employees Trend Over Months
# ============================================================================

@router.get("/all-trend")
async def get_all_trend(
    efficiency_module: Optional[str] = Query(None, description="Filter by efficiency module: TIME_BASED, QUANTITY_BASED, TASK_BASED"),
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(require_roles(["SUPERVISOR", "ADMIN"])),
):
    """
    Get efficiency trend for all employees over the last 6 months.
    
    For supervisors, defaults to their assigned efficiency module.
    For admins, shows all employees unless efficiency_module is specified.
    
    Returns: List of {month: str, avg_time_eff: float, avg_qty_eff: float, avg_task_eff: float, employee_count: int}
    """
    # For supervisors, default to their assigned module
    if current_user.role == RoleEnum.SUPERVISOR and not efficiency_module:
        efficiency_module = current_user.supervisor_efficiency_module
    
    # Get all active employees
    emp_stmt = select(Employee.id).where(Employee.is_active == True)
    emp_result = await session.execute(emp_stmt)
    employee_ids = [row[0] for row in emp_result.all()]
    
    if not employee_ids:
        return []
    
    # Get last 6 months of efficiency periods
    six_months_ago = date.today() - relativedelta(months=6)
    
    stmt = select(EfficiencyPeriod).where(
        EfficiencyPeriod.employee_id.in_(employee_ids),
        EfficiencyPeriod.period_start >= six_months_ago,
    ).order_by(EfficiencyPeriod.period_start)
    
    result = await session.execute(stmt)
    periods = result.scalars().all()
    
    # If efficiency_module is specified, filter by related job cards
    if efficiency_module:
        from app.models.models import EfficiencyTypeEnum
        try:
            eff_enum = EfficiencyTypeEnum(efficiency_module)
            
            # Get job card IDs for this efficiency module
            jc_stmt = (
                select(JobCard.employee_id, JobCard.entry_date)
                .join(ActivityCode, JobCard.activity_code_id == ActivityCode.id)
                .where(
                    ActivityCode.efficiency_type == eff_enum,
                    JobCard.entry_date >= six_months_ago,
                )
                .distinct()
            )
            jc_result = await session.execute(jc_stmt)
            relevant_employee_dates = jc_result.all()
            
            # Create a set of (employee_id, entry_date) pairs for this module
            relevant_pairs = {(emp_id, entry_date) for emp_id, entry_date in relevant_employee_dates}
            
            # Filter efficiency periods to only include those from relevant job cards
            filtered_periods = []
            for period in periods:
                # Check if this employee has any job cards in this efficiency module
                # for the period's date range
                period_date = period.period_start
                if any(emp_id == period.employee_id for emp_id, _ in relevant_pairs):
                    filtered_periods.append(period)
            
            periods = filtered_periods
            
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid efficiency_module: {efficiency_module}"
            )
    
    # For supervisors, further filter to only show operators they created
    if current_user.role == RoleEnum.SUPERVISOR:
        # Filter employees to only those created by this supervisor
        supervisor_employee_ids = set(emp.id for emp in employees if emp.created_by == current_user.id)
        
        # Filter efficiency periods to only include those from supervisor-created employees
        filtered_periods = []
        for period in periods:
            if period.employee_id in supervisor_employee_ids:
                filtered_periods.append(period)
        
        periods = filtered_periods
    
    # Group by month
    monthly_data = {}
    for period in periods:
        month_key = period.period_start.strftime('%Y-%m')
        if month_key not in monthly_data:
            monthly_data[month_key] = {
                'time_eff': [],
                'qty_eff': [],
                'task_eff': [],
                'employees': set()
            }
        
        monthly_data[month_key]['time_eff'].append(period.time_efficiency or 0)
        monthly_data[month_key]['qty_eff'].append(period.quantity_efficiency or 0)
        monthly_data[month_key]['task_eff'].append(period.task_efficiency or 0)
        monthly_data[month_key]['employees'].add(period.employee_id)
    
    # Calculate averages
    trend = []
    for month, data in sorted(monthly_data.items()):
        trend.append({
            "month": month,
            "avg_time_eff": round(sum(data['time_eff']) / len(data['time_eff']), 2) if data['time_eff'] else 0,
            "avg_qty_eff": round(sum(data['qty_eff']) / len(data['qty_eff']), 2) if data['qty_eff'] else 0,
            "avg_task_eff": round(sum(data['task_eff']) / len(data['task_eff']), 2) if data['task_eff'] else 0,
            "employee_count": len(data['employees']),
        })
    
    return trend


# ============================================================================
# GET /employee-comparison - Compare All Employees
# ============================================================================

@router.get("/employee-comparison")
async def get_employee_comparison(
    efficiency_module: Optional[str] = Query(None, description="Filter by efficiency module: TIME_BASED, QUANTITY_BASED, TASK_BASED"),
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(require_roles(["SUPERVISOR", "ADMIN"])),
):
    """
    Compare all employees' performance (current vs last month).
    Excludes supervisors and admins - only shows operators.
    
    For supervisors, defaults to their assigned efficiency module.
    For admins, shows all employees unless efficiency_module is specified.
    
    Returns: List of {employee_name: str, ec_number: str, current_month: float, last_month: float, trend: str}
    """
    
    # For supervisors, default to their assigned module
    if current_user.role == RoleEnum.SUPERVISOR and not efficiency_module:
        efficiency_module = current_user.supervisor_efficiency_module
    
    # Get all active employees (exclude SUPERVISOR and ADMIN roles)
    emp_stmt = select(Employee).where(
        Employee.is_active == True,
        Employee.role == RoleEnum.OPERATOR
    )
    emp_result = await session.execute(emp_stmt)
    employees = emp_result.scalars().all()
    
    if not employees:
        return []
    
    # Get current and last month dates
    today = date.today()
    current_month_start = date(today.year, today.month, 1)
    last_month_start = current_month_start - relativedelta(months=1)
    last_month_end = current_month_start - relativedelta(days=1)
    
    # If efficiency_module is specified, get relevant employees only
    relevant_employee_ids = set()
    if efficiency_module:
        from app.models.models import EfficiencyTypeEnum
        try:
            eff_enum = EfficiencyTypeEnum(efficiency_module)
            
            # Get employees who have job cards in this efficiency module
            jc_stmt = (
                select(JobCard.employee_id)
                .join(ActivityCode, JobCard.activity_code_id == ActivityCode.id)
                .where(
                    ActivityCode.efficiency_type == eff_enum,
                    JobCard.entry_date >= last_month_start,
                )
                .distinct()
            )
            jc_result = await session.execute(jc_stmt)
            relevant_employee_ids = set(row[0] for row in jc_result.all())
            
            # Filter employees to only those with relevant job cards
            employees = [emp for emp in employees if emp.id in relevant_employee_ids]
            
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid efficiency_module: {efficiency_module}"
            )
    
    # For supervisors, further filter to only show operators they created
    if current_user.role == RoleEnum.SUPERVISOR:
        # Filter employees to only those created by this supervisor
        employees = [emp for emp in employees if emp.created_by == current_user.id]
    
    comparisons = []
    for emp in employees:
        # Get current month efficiency
        current_stmt = select(EfficiencyPeriod).where(
            EfficiencyPeriod.employee_id == emp.id,
            EfficiencyPeriod.period_start >= current_month_start,
        )
        current_result = await session.execute(current_stmt)
        current_periods = current_result.scalars().all()
        
        # Get last month efficiency
        last_stmt = select(EfficiencyPeriod).where(
            EfficiencyPeriod.employee_id == emp.id,
            EfficiencyPeriod.period_start >= last_month_start,
            EfficiencyPeriod.period_end <= last_month_end,
        )
        last_result = await session.execute(last_stmt)
        last_periods = last_result.scalars().all()
        
        # Calculate averages (using time_efficiency as main metric)
        current_avg = (
            sum(p.time_efficiency or 0 for p in current_periods) / len(current_periods)
            if current_periods else 0
        )
        last_avg = (
            sum(p.time_efficiency or 0 for p in last_periods) / len(last_periods)
            if last_periods else 0
        )
        
        # Determine trend
        if current_avg > last_avg + 5:
            trend = 'up'
        elif current_avg < last_avg - 5:
            trend = 'down'
        else:
            trend = 'stable'
        
        comparisons.append({
            "employee_name": emp.name,
            "ec_number": emp.ec_number,
            "current_month": round(current_avg, 2),
            "last_month": round(last_avg, 2),
            "trend": trend,
        })
    
    return comparisons


# ============================================================================
# GET /employee-jobcard-summary - Job Card Status Summary per Employee
# ============================================================================

@router.get("/employee-jobcard-summary")
async def get_employee_jobcard_summary(
    start: Optional[date] = Query(None, description="Period start date (defaults to first day of current month)"),
    end: Optional[date] = Query(None, description="Period end date (defaults to today)"),
    efficiency_module: Optional[str] = Query(None, description="Filter by efficiency module: TIME_BASED, QUANTITY_BASED, TASK_BASED"),
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(require_roles(["SUPERVISOR", "ADMIN"])),
):
    """Return per-employee job card counts by approval status for the given period.

    For supervisors, defaults to their assigned efficiency module.
    For admins, shows all employees unless efficiency_module is specified.

    Used by the supervisor Employee Analytics export to include a summary sheet
    of how many job cards each employee has and how many are accepted/rejected/pending.
    """

    # For supervisors, default to their assigned module
    if current_user.role == RoleEnum.SUPERVISOR and not efficiency_module:
        efficiency_module = current_user.supervisor_efficiency_module

    # Default to current calendar month if dates not provided
    today = date.today()
    if start is None:
        start = date(today.year, today.month, 1)
    if end is None:
        end = today

    # Only active operators
    emp_stmt = select(Employee).where(
        Employee.is_active == True,
        Employee.role == RoleEnum.OPERATOR,
    )
    emp_result = await session.execute(emp_stmt)
    employees = {emp.id: emp for emp in emp_result.scalars().all()}

    if not employees:
        return []

    # Build job card query
    jc_stmt = (
        select(
            JobCard.employee_id,
            JobCard.approval_status,
            func.count(JobCard.id).label("count"),
        )
        .where(
            JobCard.employee_id.in_(employees.keys()),
            JobCard.entry_date >= start,
            JobCard.entry_date <= end,
        )
    )

    # Apply efficiency module filter if specified
    if efficiency_module:
        from app.models.models import EfficiencyTypeEnum
        try:
            eff_enum = EfficiencyTypeEnum(efficiency_module)
            jc_stmt = jc_stmt.join(ActivityCode, JobCard.activity_code_id == ActivityCode.id).where(
                ActivityCode.efficiency_type == eff_enum
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid efficiency_module: {efficiency_module}"
            )
    
    # For supervisors, further filter to only show operators they created
    if current_user.role == RoleEnum.SUPERVISOR:
        # Filter employees to only those created by this supervisor
        employees = {emp_id: emp for emp_id, emp in employees.items() if emp.created_by == current_user.id}

    jc_stmt = jc_stmt.group_by(JobCard.employee_id, JobCard.approval_status)

    jc_result = await session.execute(jc_stmt)

    # Prepare summary structure
    summary = {
        emp_id: {
            "ec_number": emp.ec_number,
            "name": emp.name,
            "total_jobcards": 0,
            "accepted_count": 0,
            "rejected_count": 0,
            "pending_count": 0,
        }
        for emp_id, emp in employees.items()
    }

    for emp_id, approval_status, count in jc_result.all():
        if emp_id not in summary:
            continue
        entry = summary[emp_id]
        entry["total_jobcards"] += int(count or 0)

        status_value = approval_status.value if hasattr(approval_status, "value") else approval_status
        if status_value == "APPROVED":
            entry["accepted_count"] += int(count or 0)
        elif status_value == "REJECTED":
            entry["rejected_count"] += int(count or 0)
        else:
            entry["pending_count"] += int(count or 0)

    return list(summary.values())
