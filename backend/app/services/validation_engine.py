"""
Job Card Validation Engine.
Checks for data quality issues and creates validation flags.
Uses modular rules and ensures idempotent flag creation.
"""

from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import List

from app.models.models import (
    JobCard,
    ValidationFlag,
    WorkOrder,
    ActivityCode,
    FlagTypeEnum,
)


class ValidationEngine:
    """
    Validation Engine for Job Cards.
    
    Runs modular validation rules and creates ValidationFlag records.
    Ensures idempotent flag creation (no duplicates).
    """
    
    def __init__(self):
        """Initialize the validation engine with all rules."""
        self.rules = [
            msd_window_rule,
            duplication_rule,
            awc_rule,
            split_candidate_rule,
            qty_mismatch_rule,
        ]
    
    async def run_for_jobcard(
        self, 
        jobcard: JobCard, 
        session: AsyncSession
    ) -> List[ValidationFlag]:
        """
        Run all validation rules for a job card.
        
        Creates ValidationFlag records in DB if issues are found.
        Ensures idempotence - won't create duplicate flags.
        
        Args:
            jobcard: The job card to validate
            session: Async database session
            
        Returns:
            List of created ValidationFlag objects
        """
        all_flags = []
        
        # Run each rule
        for rule in self.rules:
            flags = await rule(jobcard, session)
            all_flags.extend(flags)
        
        # Remove existing unresolved flags for this job card to ensure idempotence
        await self._clear_existing_flags(jobcard.id, session)
        
        # Save new flags
        for flag in all_flags:
            session.add(flag)
        
        await session.commit()
        
        return all_flags
    
    async def _clear_existing_flags(
        self, 
        job_card_id: int, 
        session: AsyncSession
    ) -> None:
        """
        Delete existing unresolved flags for a job card.
        Ensures idempotent flag creation.
        """
        statement = select(ValidationFlag).where(
            ValidationFlag.job_card_id == job_card_id,
            ValidationFlag.resolved == False
        )
        result = await session.execute(statement)
        existing_flags = result.scalars().all()
        
        for flag in existing_flags:
            await session.delete(flag)


# ============================================================================
# VALIDATION RULES
# Each rule returns List[ValidationFlag] (can be empty list)
# ============================================================================


async def msd_window_rule(
    jobcard: JobCard, 
    session: AsyncSession
) -> List[ValidationFlag]:
    """
    Rule 1: MSD Window Check
    
    Computes payroll month window: 25th of previous month → 10th of current month.
    If entry_date is outside this window, create OUTSIDE_MSD flag.
    
    Example: 
    - MSD month 2024-11 means window is 2024-10-25 to 2024-11-10
    """
    # Get work order to determine MSD month
    statement = select(WorkOrder).where(WorkOrder.id == jobcard.work_order_id)
    result = await session.execute(statement)
    work_order = result.scalar_one_or_none()
    
    if not work_order:
        return []
    
    # Parse MSD month (format: YYYY-MM)
    msd_year, msd_month = map(int, work_order.msd_month.split('-'))
    
    # Calculate MSD window: 25th prev month → 10th current month
    msd_date = date(msd_year, msd_month, 1)
    
    # Start: 25th of previous month
    prev_month = msd_date - relativedelta(months=1)
    window_start = date(prev_month.year, prev_month.month, 25)
    
    # End: 10th of current month
    window_end = date(msd_year, msd_month, 10)
    
    # Check if entry_date is outside window
    if jobcard.entry_date < window_start or jobcard.entry_date > window_end:
        return [
            ValidationFlag(
                job_card_id=jobcard.id,
                flag_type=FlagTypeEnum.OUTSIDE_MSD,
                details=f"Entry date {jobcard.entry_date} is outside MSD window "
                       f"{window_start} to {window_end} for month {work_order.msd_month}",
                resolved=False,
            )
        ]
    
    return []


async def duplication_rule(
    jobcard: JobCard, 
    session: AsyncSession
) -> List[ValidationFlag]:
    """
    Rule 2: Duplication Check
    
    Search for job cards in the same MSD month with same:
    - machine_id
    - work_order_id
    - activity_code_id
    
    If found, return DUPLICATION flag with evidence.
    """
    # Get work order to find MSD month
    statement = select(WorkOrder).where(WorkOrder.id == jobcard.work_order_id)
    result = await session.execute(statement)
    work_order = result.scalar_one_or_none()
    
    if not work_order:
        return []
    
    msd_month = work_order.msd_month
    
    # Find all work orders in same MSD month
    wo_statement = select(WorkOrder.id).where(WorkOrder.msd_month == msd_month)
    wo_result = await session.execute(wo_statement)
    wo_ids_in_month = [row[0] for row in wo_result.all()]
    
    # Search for duplicates
    dup_statement = select(JobCard).where(
        JobCard.id != jobcard.id,  # Exclude current job card
        JobCard.work_order_id.in_(wo_ids_in_month),  # Same MSD month
        JobCard.machine_id == jobcard.machine_id,
        JobCard.work_order_id == jobcard.work_order_id,
        JobCard.activity_code_id == jobcard.activity_code_id,
    )
    
    dup_result = await session.execute(dup_statement)
    duplicates = dup_result.scalars().all()
    
    if duplicates:
        evidence = [f"JobCard ID {jc.id} (date: {jc.entry_date})" for jc in duplicates[:3]]
        evidence_str = ", ".join(evidence)
        if len(duplicates) > 3:
            evidence_str += f" and {len(duplicates) - 3} more"
        
        return [
            ValidationFlag(
                job_card_id=jobcard.id,
                flag_type=FlagTypeEnum.DUPLICATION,
                details=f"Found {len(duplicates)} duplicate(s) in MSD month {msd_month} "
                       f"with same machine/WO/activity: {evidence_str}",
                resolved=False,
            )
        ]
    
    return []


async def awc_rule(
    jobcard: JobCard, 
    session: AsyncSession
) -> List[ValidationFlag]:
    """
    Rule 3: AWC (Actual Without Completion) Check
    
    If activity_code_id is None, return AWC flag.
    This indicates work was done but no proper activity was assigned.
    """
    if jobcard.activity_code_id is None:
        return [
            ValidationFlag(
                job_card_id=jobcard.id,
                flag_type=FlagTypeEnum.AWC,
                details=f"AWC detected: Job card has {jobcard.actual_hours} hours "
                       f"but no activity_code_id assigned",
                resolved=False,
            )
        ]
    
    return []


async def split_candidate_rule(
    jobcard: JobCard, 
    session: AsyncSession
) -> List[ValidationFlag]:
    """
    Rule 4: Split Candidate Check
    
    If status == 'IC' and there exists a record for same work_order + activity_code
    with status 'C' by a different employee, mark BOTH as SPLIT_CANDIDATE.
    
    This suggests the work might have been split between employees.
    """
    if jobcard.status.value != 'IC':
        return []
    
    # Find completed job cards with same WO and activity by different employees
    statement = select(JobCard).where(
        JobCard.id != jobcard.id,
        JobCard.work_order_id == jobcard.work_order_id,
        JobCard.activity_code_id == jobcard.activity_code_id,
        JobCard.status == 'C',
        JobCard.employee_id != jobcard.employee_id,
    )
    
    result = await session.execute(statement)
    completed_by_others = result.scalars().all()
    
    if completed_by_others:
        flags = []
        
        # Flag the current job card
        other_ids = [str(jc.id) for jc in completed_by_others[:3]]
        other_ids_str = ", ".join(other_ids)
        
        flags.append(
            ValidationFlag(
                job_card_id=jobcard.id,
                flag_type=FlagTypeEnum.SPLIT_CANDIDATE,
                details=f"Status=IC but related job card(s) {other_ids_str} are Complete "
                       f"by different employee(s) - possible work split",
                resolved=False,
            )
        )
        
        # Flag the other job cards too
        for other_jc in completed_by_others:
            flags.append(
                ValidationFlag(
                    job_card_id=other_jc.id,
                    flag_type=FlagTypeEnum.SPLIT_CANDIDATE,
                    details=f"Status=C but related job card {jobcard.id} is Incomplete "
                           f"by different employee - possible work split",
                    resolved=False,
                )
            )
        
        return flags
    
    return []


async def qty_mismatch_rule(
    jobcard: JobCard, 
    session: AsyncSession
) -> List[ValidationFlag]:
    """
    Rule 5: Quantity Mismatch Check
    
    If jobcard.qty > work_order.planned_qty, return QTY_MISMATCH flag.
    Also checks if total quantities across all job cards exceed planned.
    """
    # Get work order
    statement = select(WorkOrder).where(WorkOrder.id == jobcard.work_order_id)
    result = await session.execute(statement)
    work_order = result.scalar_one_or_none()
    
    if not work_order:
        return []
    
    flags = []
    
    # Check 1: Single job card quantity exceeds planned
    if jobcard.qty > work_order.planned_qty:
        flags.append(
            ValidationFlag(
                job_card_id=jobcard.id,
                flag_type=FlagTypeEnum.QTY_MISMATCH,
                details=f"Job card quantity ({jobcard.qty}) exceeds work order "
                       f"planned quantity ({work_order.planned_qty})",
                resolved=False,
            )
        )
    
    # Check 2: Total quantities across all job cards exceed planned (with 10% tolerance)
    total_statement = select(JobCard).where(
        JobCard.work_order_id == jobcard.work_order_id
    )
    total_result = await session.execute(total_statement)
    all_job_cards = total_result.scalars().all()
    
    total_qty = sum(jc.qty for jc in all_job_cards)
    tolerance = work_order.planned_qty * 1.1  # 10% over
    
    if total_qty > tolerance:
        flags.append(
            ValidationFlag(
                job_card_id=jobcard.id,
                flag_type=FlagTypeEnum.QTY_MISMATCH,
                details=f"Total quantity across all job cards ({total_qty}) exceeds "
                       f"planned ({work_order.planned_qty}) by more than 10%",
                resolved=False,
            )
        )
    
    return flags


# ============================================================================
# SYNC WRAPPER FOR BACKWARD COMPATIBILITY
# Use these in sync routes until routes are migrated to async
# ============================================================================

def validate_job_card(jobcard: JobCard, session) -> List[ValidationFlag]:
    """
    Synchronous wrapper for validation engine.
    
    This is a temporary compatibility function for sync routes.
    TODO: Migrate routes to async and use ValidationEngine directly.
    
    Args:
        jobcard: The job card to validate
        session: Synchronous database session
        
    Returns:
        List of created ValidationFlag objects (empty for now)
    """
    # For now, return empty list since we can't run async code in sync context
    # This allows the app to run without errors
    # Real validation should be done by migrating routes to async
    print(f"WARNING: Sync validation called for jobcard {jobcard.id}. "
          "Migrate to async routes for full validation.")
    return []


def revalidate_job_card(job_card_id: int, session) -> List[ValidationFlag]:
    """
    Synchronous wrapper for revalidation.
    
    Temporary compatibility function for sync routes.
    """
    print(f"WARNING: Sync revalidation called for jobcard {job_card_id}. "
          "Migrate to async routes for full validation.")
    return []
