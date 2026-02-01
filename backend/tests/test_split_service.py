"""
Unit tests for split_service.compute_splits_for_workorder
"""

import pytest
from datetime import datetime, date
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.models.models import (
    JobCard,
    ValidationFlag,
    WorkOrder,
    ActivityCode,
    FlagTypeEnum,
    JobCardStatusEnum,
    SourceEnum,
)
from app.services.split_service import compute_splits_for_workorder


@pytest.fixture(scope="function")
async def async_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session
    await engine.dispose()


async def _seed_basic(async_session: AsyncSession):
    # Work order
    wo = WorkOrder(wo_number="WO-1", machine_id=1, planned_qty=100.0, msd_month="2024-11")
    async_session.add(wo)
    await async_session.commit()
    await async_session.refresh(wo)

    # Activity
    act = ActivityCode(
        code="ACT1",
        description="Activity 1",
        efficiency_type="TIME_BASED",
        std_hours_per_unit=0.5,
        std_qty_per_hour=None,
        last_updated=datetime.utcnow(),
    )
    async_session.add(act)
    await async_session.commit()
    await async_session.refresh(act)

    return wo, act


@pytest.mark.asyncio
async def test_returns_empty_when_no_flags(async_session: AsyncSession):
    wo, act = await _seed_basic(async_session)

    # Two jobcards but no flags
    jc1 = JobCard(
        employee_id=1,
        machine_id=1,
        work_order_id=wo.id,
        activity_code_id=act.id,
        activity_desc="Work",
        qty=10,
        actual_hours=5,
        status=JobCardStatusEnum.C,
        entry_date=date(2024, 11, 5),
        source=SourceEnum.TECHNICIAN,
    )
    jc2 = JobCard(
        employee_id=2,
        machine_id=1,
        work_order_id=wo.id,
        activity_code_id=act.id,
        activity_desc="Work",
        qty=20,
        actual_hours=15,
        status=JobCardStatusEnum.C,
        entry_date=date(2024, 11, 6),
        source=SourceEnum.TECHNICIAN,
    )
    async_session.add_all([jc1, jc2])
    await async_session.commit()
    await async_session.refresh(jc1)
    await async_session.refresh(jc2)

    allocations = await compute_splits_for_workorder(wo.id, async_session)
    assert allocations == []


@pytest.mark.asyncio
async def test_basic_allocation(async_session: AsyncSession):
    wo, act = await _seed_basic(async_session)

    # Two participants
    jc1 = JobCard(
        employee_id=1,
        machine_id=1,
        work_order_id=wo.id,
        activity_code_id=act.id,
        activity_desc="Work",
        qty=10,              # 10 * 0.5 = 5 std hours contribution
        actual_hours=5,      # 25% of actuals
        status=JobCardStatusEnum.C,
        entry_date=date(2024, 11, 5),
        source=SourceEnum.TECHNICIAN,
    )
    jc2 = JobCard(
        employee_id=2,
        machine_id=1,
        work_order_id=wo.id,
        activity_code_id=act.id,
        activity_desc="Work",
        qty=20,              # 20 * 0.5 = 10 std hours contribution
        actual_hours=15,     # 75% of actuals
        status=JobCardStatusEnum.C,
        entry_date=date(2024, 11, 6),
        source=SourceEnum.TECHNICIAN,
    )
    async_session.add_all([jc1, jc2])
    await async_session.commit()
    await async_session.refresh(jc1)
    await async_session.refresh(jc2)

    # Mark both as split candidates (unresolved)
    f1 = ValidationFlag(job_card_id=jc1.id, flag_type=FlagTypeEnum.SPLIT_CANDIDATE, details="", resolved=False)
    f2 = ValidationFlag(job_card_id=jc2.id, flag_type=FlagTypeEnum.SPLIT_CANDIDATE, details="", resolved=False)
    async_session.add_all([f1, f2])
    await async_session.commit()

    allocations = await compute_splits_for_workorder(wo.id, async_session)

    # total_std = (10+20) * 0.5 = 15
    # total_actual = 5 + 15 = 20
    # emp1 credit = 15 * (5/20) = 3.75
    # emp2 credit = 15 * (15/20) = 11.25
    assert len(allocations) == 2
    a1 = next(a for a in allocations if a["employee_id"] == 1)
    a2 = next(a for a in allocations if a["employee_id"] == 2)
    assert abs(a1["credit_hours"] - 3.75) < 1e-6
    assert abs(a2["credit_hours"] - 11.25) < 1e-6
    # Percent by actuals: 25% and 75%
    assert abs(a1["credit_pct"] - 0.25) < 1e-6
    assert abs(a2["credit_pct"] - 0.75) < 1e-6


@pytest.mark.asyncio
async def test_aggregate_across_activities(async_session: AsyncSession):
    wo, act1 = await _seed_basic(async_session)

    # Second activity
    act2 = ActivityCode(
        code="ACT2",
        description="Activity 2",
        efficiency_type="TIME_BASED",
        std_hours_per_unit=1.0,
        std_qty_per_hour=None,
        last_updated=datetime.utcnow(),
    )
    async_session.add(act2)
    await async_session.commit()
    await async_session.refresh(act2)

    # Employee 1 contributes on act1 and act2
    jc1 = JobCard(
        employee_id=1,
        machine_id=1,
        work_order_id=wo.id,
        activity_code_id=act1.id,
        activity_desc="Work a1",
        qty=10,
        actual_hours=5,
        status=JobCardStatusEnum.C,
        entry_date=date(2024, 11, 5),
        source=SourceEnum.TECHNICIAN,
    )
    jc2 = JobCard(
        employee_id=1,
        machine_id=1,
        work_order_id=wo.id,
        activity_code_id=act2.id,
        activity_desc="Work a2",
        qty=5,
        actual_hours=5,
        status=JobCardStatusEnum.C,
        entry_date=date(2024, 11, 6),
        source=SourceEnum.TECHNICIAN,
    )
    # Employee 2 contributes only on act1
    jc3 = JobCard(
        employee_id=2,
        machine_id=1,
        work_order_id=wo.id,
        activity_code_id=act1.id,
        activity_desc="Work a1",
        qty=20,
        actual_hours=15,
        status=JobCardStatusEnum.C,
        entry_date=date(2024, 11, 6),
        source=SourceEnum.TECHNICIAN,
    )
    async_session.add_all([jc1, jc2, jc3])
    await async_session.commit()
    await async_session.refresh(jc1)
    await async_session.refresh(jc2)
    await async_session.refresh(jc3)

    # Flags for all
    for jc in (jc1, jc2, jc3):
        async_session.add(ValidationFlag(job_card_id=jc.id, flag_type=FlagTypeEnum.SPLIT_CANDIDATE, details="", resolved=False))
    await async_session.commit()

    allocations = await compute_splits_for_workorder(wo.id, async_session)

    # Act1: std_per_unit=0.5, qty sum = 30 => total_std_1 = 15, actual=20 => emp1=3.75, emp2=11.25
    # Act2: std_per_unit=1.0, qty sum = 5  => total_std_2 = 5,  actual=5  => emp1=5
    # Aggregated: emp1=8.75, emp2=11.25
    a1 = next(a for a in allocations if a["employee_id"] == 1)
    a2 = next(a for a in allocations if a["employee_id"] == 2)
    assert abs(a1["credit_hours"] - 8.75) < 1e-6
    assert abs(a2["credit_hours"] - 11.25) < 1e-6
