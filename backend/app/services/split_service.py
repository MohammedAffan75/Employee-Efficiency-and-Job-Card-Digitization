"""
Split allocation service.
Computes split credits for a work order based on split candidate job cards.
"""

from __future__ import annotations

from collections import defaultdict
from typing import List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.models import (
    JobCard,
    ValidationFlag,
    FlagTypeEnum,
    ActivityCode,
)


async def compute_splits_for_workorder(work_order_id: int, session: AsyncSession) -> List[Dict[str, Any]]:
    """
    Compute split allocation for a given work order.

    Steps:
    - Find jobcards for the work order that are marked as SPLIT_CANDIDATE (unresolved flags)
    - Group by (activity_code_id) and include only those with activity_code_id not null
    - For each group, compute:
        - total_actual_hours = sum(actual_hours)
        - total_std_hours = sum(ActivityCode.std_hours_per_unit * qty) (treat None as 0)
        - For each employee: credit = total_std_hours * (employee_actual_hours / total_actual_hours)
    - Aggregate credits per employee across all groups in the work order

    Returns:
        List of dicts: {employee_id, actual_hours, credit_hours, credit_pct}
    """
    # Find jobcards in this work order that have unresolved SPLIT_CANDIDATE flags
    flagged_stmt = select(JobCard).join(
        ValidationFlag, ValidationFlag.job_card_id == JobCard.id
    ).where(
        JobCard.work_order_id == work_order_id,
        ValidationFlag.flag_type == FlagTypeEnum.SPLIT_CANDIDATE,
        ValidationFlag.resolved == False,
    )
    result = await session.execute(flagged_stmt)
    flagged_jobcards: list[JobCard] = result.scalars().all()

    if not flagged_jobcards:
        return []

    # Load activity codes referenced by these jobcards
    activity_ids = {jc.activity_code_id for jc in flagged_jobcards if jc.activity_code_id is not None}
    activities: dict[int, ActivityCode] = {}
    if activity_ids:
        act_stmt = select(ActivityCode).where(ActivityCode.id.in_(activity_ids))
        act_res = await session.execute(act_stmt)
        for act in act_res.scalars().all():
            activities[act.id] = act

    # Group jobcards by activity_code_id
    groups: dict[int, list[JobCard]] = defaultdict(list)
    for jc in flagged_jobcards:
        if jc.activity_code_id is not None:
            groups[jc.activity_code_id].append(jc)

    # Aggregate per employee across all groups
    employee_actual_sum: dict[int, float] = defaultdict(float)
    employee_credit_sum: dict[int, float] = defaultdict(float)

    for activity_id, jcs in groups.items():
        # Compute totals for this group
        total_actual = sum((jc.actual_hours or 0.0) for jc in jcs)
        # Standard hours based on activity standard per unit * qty
        std_per_unit = (activities.get(activity_id).std_hours_per_unit if activities.get(activity_id) else 0.0) or 0.0
        total_std = sum(((jc.qty or 0.0) * std_per_unit) for jc in jcs)

        if total_actual <= 0:
            # If no actuals, skip credit allocation for this group
            continue

        # Distribute credits proportionally to actual hours
        for jc in jcs:
            if jc.employee_id is None:
                continue
            emp_actual = jc.actual_hours or 0.0
            credit = total_std * (emp_actual / total_actual)
            employee_actual_sum[jc.employee_id] += emp_actual
            employee_credit_sum[jc.employee_id] += credit

    # Compute credit percentage based on total actuals within all groups considered
    grand_total_actual = sum(employee_actual_sum.values()) or 1.0

    allocations: List[Dict[str, Any]] = []
    for emp_id, emp_actual in employee_actual_sum.items():
        credit_hours = employee_credit_sum[emp_id]
        credit_pct = (emp_actual / grand_total_actual) if grand_total_actual else 0.0
        allocations.append(
            {
                "employee_id": emp_id,
                "actual_hours": round(emp_actual, 4),
                "credit_hours": round(credit_hours, 4),
                "credit_pct": round(credit_pct, 6),
            }
        )

    # Sort by credit_hours desc for readability
    allocations.sort(key=lambda x: x["credit_hours"], reverse=True)
    return allocations
