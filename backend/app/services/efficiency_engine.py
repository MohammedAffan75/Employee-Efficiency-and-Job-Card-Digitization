"""
Efficiency computation engine.
Provides functions to compute employee and team efficiencies for a period.
"""

from __future__ import annotations

from datetime import date
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.models import (
    JobCard,
    ActivityCode,
    EfficiencyEmployee,
    EfficiencyPeriod,
    EfficiencyTypeEnum,
)

EPS = 1e-6


async def _fetch_employee_jobcards(
    employee_id: int,
    period_start: date,
    period_end: date,
    session: AsyncSession,
):
    stmt = (
        select(JobCard, ActivityCode)
        .outerjoin(ActivityCode, JobCard.activity_code_id == ActivityCode.id)
        .where(
            JobCard.employee_id == employee_id,
            JobCard.entry_date >= period_start,
            JobCard.entry_date <= period_end,
        )
    )
    result = await session.execute(stmt)
    return result.all()  # list of tuples (JobCard, ActivityCode)


async def compute_employee_efficiency(
    employee_id: int,
    period_start: date,
    period_end: date,
    session: AsyncSession,
) -> Dict[str, Any]:
    """
    Compute on-demand efficiency metrics for an employee and upsert EfficiencyPeriod.

    - total_actual_productive_hours: sum of actual_hours with a valid activity_code
    - standard_hours_allowed: sum(activity.std_hours_per_unit * job.qty) when std_hours_per_unit provided
    - time_efficiency: standard_hours_allowed / productive_hours * 100
    - task_efficiency: tasks_completed / tasks_planned (fallbacks documented below)
    - quantity_efficiency: For QUANTITY_BASED activities: actual_qty / (std_qty_per_hour * actual_hours)
                           Here we treat job.qty as quantity achieved
    - awc_pct: awc_hours / (awc_hours + productive_hours)
    - If awc_pct > 0.5 -> compute_team_average and return that instead
    - Upsert into EfficiencyPeriod
    """
    # Fetch data
    rows = await _fetch_employee_jobcards(employee_id, period_start, period_end, session)

    productive_hours = 0.0
    awc_hours = 0.0
    standard_hours_allowed = 0.0

    # Task metrics placeholders
    tasks_completed = 0
    tasks_planned: Optional[int] = None  # If a task plan exists, plug it in when available

    # Quantity efficiency accumulators
    qty_eff_sum = 0.0
    qty_eff_count = 0

    for jc, act in rows:
        hours = float(jc.actual_hours or 0.0)
        qty = float(jc.qty or 0.0)

        if jc.activity_code_id is None or act is None:
            awc_hours += hours
            continue

        productive_hours += hours

        # Standard hours from TIME/TASK activities using std_hours_per_unit
        std_h = float((act.std_hours_per_unit or 0.0) * qty)
        standard_hours_allowed += std_h

        # Task efficiency proxy: use jobcard count as completed unit
        if act.efficiency_type == EfficiencyTypeEnum.TASK_BASED:
            tasks_completed += 1

        # Quantity efficiency for quantity-based activities
        if act.efficiency_type == EfficiencyTypeEnum.QUANTITY_BASED:
            denom = max(float(act.std_qty_per_hour or 0.0) * max(hours, 0.0), EPS)
            qty_eff = qty / denom
            qty_eff_sum += qty_eff
            qty_eff_count += 1

    # Fallbacks
    if tasks_planned is None:
        # Use count of jobcards as both completed and planned as a simple baseline
        tasks_planned = max(tasks_completed, 1)

    total_hours = productive_hours + awc_hours
    awc_pct = (awc_hours / max(total_hours, EPS)) if total_hours > 0 else 0.0

    time_efficiency = (standard_hours_allowed / max(productive_hours, EPS)) * 100.0
    task_efficiency = (tasks_completed / max(tasks_planned, 1)) * 100.0
    quantity_efficiency = (qty_eff_sum / max(qty_eff_count, 1)) * 100.0

    # If AWC > 50%, previously returned team average; now always return individual's numbers
    team_metrics: Optional[Dict[str, Any]] = None

    # Prepare final payload
    payload = team_metrics or {
        "employee_id": employee_id,
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "time_efficiency": round(time_efficiency, 2),
        "task_efficiency": round(task_efficiency, 2),
        "quantity_efficiency": round(quantity_efficiency, 2),
        "awc_pct": round(awc_pct, 4),
        "standard_hours_allowed": round(standard_hours_allowed, 2),
        "actual_hours": round(productive_hours, 2),
    }

    # Upsert EfficiencyPeriod (store what we returned)
    await _upsert_efficiency_period(
        employee_id=employee_id,
        period_start=period_start,
        period_end=period_end,
        data=payload,
        session=session,
    )

    return payload


async def compute_team_average(
    team: Optional[str],
    period_start: date,
    period_end: date,
    session: AsyncSession,
) -> Dict[str, Any]:
    """
    Average the EfficiencyPeriod metrics for all employees in a team within a period.
    Excludes employees whose AWC% is already > 50%.
    If no employees match, return zeros.
    """
    if not team:
        return {
            "employee_id": None,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "time_efficiency": 0.0,
            "task_efficiency": 0.0,
            "quantity_efficiency": 0.0,
            "awc_pct": 0.0,
            "standard_hours_allowed": 0.0,
            "actual_hours": 0.0,
            "team": None,
        }

    # Find team members
    emp_stmt = select(EfficiencyEmployee.id).where(EfficiencyEmployee.team == team)
    emp_res = await session.execute(emp_stmt)
    emp_ids = [row[0] for row in emp_res.all()]

    if not emp_ids:
        return {
            "employee_id": None,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "time_efficiency": 0.0,
            "task_efficiency": 0.0,
            "quantity_efficiency": 0.0,
            "awc_pct": 0.0,
            "standard_hours_allowed": 0.0,
            "actual_hours": 0.0,
            "team": team,
        }

    # Fetch their EfficiencyPeriod rows for the period
    stmt = select(EfficiencyPeriod).where(
        EfficiencyPeriod.employee_id.in_(emp_ids),
        EfficiencyPeriod.period_start == period_start,
        EfficiencyPeriod.period_end == period_end,
        EfficiencyPeriod.awc_pct <= 0.5,
    )
    res = await session.execute(stmt)
    periods = res.scalars().all()

    if not periods:
        return {
            "employee_id": None,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "time_efficiency": 0.0,
            "task_efficiency": 0.0,
            "quantity_efficiency": 0.0,
            "awc_pct": 0.0,
            "standard_hours_allowed": 0.0,
            "actual_hours": 0.0,
            "team": team,
        }

    n = len(periods)
    time_eff = sum(p.time_efficiency or 0.0 for p in periods) / n
    task_eff = sum(p.task_efficiency or 0.0 for p in periods) / n
    qty_eff = sum(p.quantity_efficiency or 0.0 for p in periods) / n
    awc = sum(p.awc_pct or 0.0 for p in periods) / n
    std_hours = sum(p.standard_hours_allowed or 0.0 for p in periods)
    actual_hours = sum(p.actual_hours or 0.0 for p in periods)

    return {
        "employee_id": None,
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "time_efficiency": round(time_eff, 2),
        "task_efficiency": round(task_eff, 2),
        "quantity_efficiency": round(qty_eff, 2),
        "awc_pct": round(awc, 4),
        "standard_hours_allowed": round(std_hours, 2),
        "actual_hours": round(actual_hours, 2),
        "team": team,
    }


async def _upsert_efficiency_period(
    employee_id: int,
    period_start: date,
    period_end: date,
    data: Dict[str, Any],
    session: AsyncSession,
) -> None:
    stmt = select(EfficiencyPeriod).where(
        EfficiencyPeriod.employee_id == employee_id,
        EfficiencyPeriod.period_start == period_start,
        EfficiencyPeriod.period_end == period_end,
    )
    res = await session.execute(stmt)
    existing_records = res.scalars().all()
    
    # Handle duplicate records (clean up if multiple exist)
    if len(existing_records) > 1:
        # Keep the first, delete the rest
        for dup in existing_records[1:]:
            await session.delete(dup)
        existing = existing_records[0]
    elif len(existing_records) == 1:
        existing = existing_records[0]
    else:
        existing = None

    if existing:
        existing.time_efficiency = float(data.get("time_efficiency") or 0.0)
        existing.task_efficiency = float(data.get("task_efficiency") or 0.0)
        existing.quantity_efficiency = float(data.get("quantity_efficiency") or 0.0)
        existing.awc_pct = float(data.get("awc_pct") or 0.0)
        existing.standard_hours_allowed = float(data.get("standard_hours_allowed") or 0.0)
        existing.actual_hours = float(data.get("actual_hours") or 0.0)
        session.add(existing)
    else:
        rec = EfficiencyPeriod(
            employee_id=employee_id,
            period_start=period_start,
            period_end=period_end,
            time_efficiency=float(data.get("time_efficiency") or 0.0),
            task_efficiency=float(data.get("task_efficiency") or 0.0),
            quantity_efficiency=float(data.get("quantity_efficiency") or 0.0),
            awc_pct=float(data.get("awc_pct") or 0.0),
            standard_hours_allowed=float(data.get("standard_hours_allowed") or 0.0),
            actual_hours=float(data.get("actual_hours") or 0.0),
        )
        session.add(rec)

    await session.commit()
