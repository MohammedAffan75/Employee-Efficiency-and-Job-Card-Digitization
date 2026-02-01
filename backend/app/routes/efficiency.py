"""
Efficiency computation endpoints.
"""

from datetime import date
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.security import get_current_user, require_roles
from app.models.models import EfficiencyEmployee
from app.services.efficiency_engine import compute_employee_efficiency

router = APIRouter()


@router.get("/{employee_id}")
async def get_employee_efficiency(
    employee_id: int,
    start: date = Query(..., description="Period start (YYYY-MM-DD)"),
    end: date = Query(..., description="Period end (YYYY-MM-DD)"),
    session: AsyncSession = Depends(get_async_session),
    current_user: EfficiencyEmployee = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Compute employee efficiency for the given period and return it.

    - Computes on demand and upserts into EfficiencyPeriod
    - If the employee's AWC% > 0.5, returns team average instead
    - Requires authenticated user (any role). Supervisors can query their team members.
    """
    # If non-admin/supervisor is querying someone else, deny
    if current_user.role.value not in ("ADMIN", "SUPERVISOR") and current_user.id != employee_id:
        raise HTTPException(status_code=403, detail="Not authorized to view other employees' efficiency")

    return await compute_employee_efficiency(employee_id, start, end, session)
