"""
Splits routes for computing per-employee credit allocation on a work order.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.security import require_roles, get_current_user
from app.models.models import EfficiencyEmployee, WorkOrder
from app.services.split_service import compute_splits_for_workorder

router = APIRouter()


@router.get("/{work_order_id}", response_model=List[dict])
async def get_splits(
    work_order_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: EfficiencyEmployee = Depends(require_roles(["SUPERVISOR", "ADMIN"])),
) -> List[Dict[str, Any]]:
    """
    Compute and return split allocations for a work order.
    Requires SUPERVISOR or ADMIN role.
    """
    wo = await session.get(WorkOrder, work_order_id)
    if not wo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work order not found")

    allocations = await compute_splits_for_workorder(work_order_id, session)
    return allocations
