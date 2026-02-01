"""
Unit tests for validation engine rules.
Tests each rule independently using pytest and async test fixtures.
"""

import pytest
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, select

from app.models.models import (
    JobCard,
    ValidationFlag,
    WorkOrder,
    Machine,
    ActivityCode,
    EfficiencyEmployee,
    FlagTypeEnum,
    JobCardStatusEnum,
    SourceEnum,
    EfficiencyTypeEnum,
    RoleEnum,
)
from app.services.validation_engine import (
    ValidationEngine,
    msd_window_rule,
    duplication_rule,
    awc_rule,
    split_candidate_rule,
    qty_mismatch_rule,
)


# ============================================================================
# TEST DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
async def async_engine():
    """Create an async SQLite engine for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def async_session(async_engine):
    """Create an async session for testing."""
    async_session_maker = sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_maker() as session:
        yield session


@pytest.fixture
async def sample_machine(async_session: AsyncSession):
    """Create a sample machine for testing."""
    machine = Machine(
        machine_code="TEST-M001",
        description="Test Machine",
        work_center="WC-TEST",
    )
    async_session.add(machine)
    await async_session.commit()
    await async_session.refresh(machine)
    return machine


@pytest.fixture
async def sample_employee(async_session: AsyncSession):
    """Create a sample employee for testing."""
    employee = EfficiencyEmployee(
        ec_number="TEST001",
        name="Test Employee",
        hashed_password="dummy_hash",
        role=RoleEnum.OPERATOR,
        team="Test Team",
        join_date=date.today(),
        is_active=True,
    )
    async_session.add(employee)
    await async_session.commit()
    await async_session.refresh(employee)
    return employee


@pytest.fixture
async def sample_activity_code(async_session: AsyncSession):
    """Create a sample activity code for testing."""
    activity = ActivityCode(
        code="ACT001",
        description="Test Activity",
        efficiency_type=EfficiencyTypeEnum.QUANTITY_BASED,
        std_qty_per_hour=10.0,
        last_updated=datetime.utcnow(),
    )
    async_session.add(activity)
    await async_session.commit()
    await async_session.refresh(activity)
    return activity


@pytest.fixture
async def sample_work_order(async_session: AsyncSession, sample_machine):
    """Create a sample work order for testing."""
    work_order = WorkOrder(
        wo_number="WO-TEST-001",
        machine_id=sample_machine.id,
        planned_qty=100.0,
        msd_month="2024-11",
    )
    async_session.add(work_order)
    await async_session.commit()
    await async_session.refresh(work_order)
    return work_order


# ============================================================================
# TEST: MSD Window Rule
# ============================================================================

@pytest.mark.asyncio
async def test_msd_window_rule_inside_window(
    async_session: AsyncSession,
    sample_work_order,
    sample_employee,
    sample_activity_code,
):
    """Test that dates inside MSD window pass validation."""
    # MSD month 2024-11 means window: 2024-10-25 to 2024-11-10
    jobcard = JobCard(
        employee_id=sample_employee.id,
        machine_id=sample_work_order.machine_id,
        work_order_id=sample_work_order.id,
        activity_code_id=sample_activity_code.id,
        activity_desc="Test work",
        qty=10.0,
        actual_hours=5.0,
        status=JobCardStatusEnum.C,
        entry_date=date(2024, 11, 5),  # Inside window
        source=SourceEnum.TECHNICIAN,
    )
    async_session.add(jobcard)
    await async_session.commit()
    await async_session.refresh(jobcard)
    
    flags = await msd_window_rule(jobcard, async_session)
    
    assert len(flags) == 0, "Date inside window should not create flag"


@pytest.mark.asyncio
async def test_msd_window_rule_before_window(
    async_session: AsyncSession,
    sample_work_order,
    sample_employee,
    sample_activity_code,
):
    """Test that dates before MSD window create flag."""
    jobcard = JobCard(
        employee_id=sample_employee.id,
        machine_id=sample_work_order.machine_id,
        work_order_id=sample_work_order.id,
        activity_code_id=sample_activity_code.id,
        activity_desc="Test work",
        qty=10.0,
        actual_hours=5.0,
        status=JobCardStatusEnum.C,
        entry_date=date(2024, 10, 20),  # Before window start (Oct 25)
        source=SourceEnum.TECHNICIAN,
    )
    async_session.add(jobcard)
    await async_session.commit()
    await async_session.refresh(jobcard)
    
    flags = await msd_window_rule(jobcard, async_session)
    
    assert len(flags) == 1
    assert flags[0].flag_type == FlagTypeEnum.OUTSIDE_MSD
    assert "2024-10-20" in flags[0].details


@pytest.mark.asyncio
async def test_msd_window_rule_after_window(
    async_session: AsyncSession,
    sample_work_order,
    sample_employee,
    sample_activity_code,
):
    """Test that dates after MSD window create flag."""
    jobcard = JobCard(
        employee_id=sample_employee.id,
        machine_id=sample_work_order.machine_id,
        work_order_id=sample_work_order.id,
        activity_code_id=sample_activity_code.id,
        activity_desc="Test work",
        qty=10.0,
        actual_hours=5.0,
        status=JobCardStatusEnum.C,
        entry_date=date(2024, 11, 15),  # After window end (Nov 10)
        source=SourceEnum.TECHNICIAN,
    )
    async_session.add(jobcard)
    await async_session.commit()
    await async_session.refresh(jobcard)
    
    flags = await msd_window_rule(jobcard, async_session)
    
    assert len(flags) == 1
    assert flags[0].flag_type == FlagTypeEnum.OUTSIDE_MSD
    assert "2024-11-15" in flags[0].details


# ============================================================================
# TEST: Duplication Rule
# ============================================================================

@pytest.mark.asyncio
async def test_duplication_rule_no_duplicates(
    async_session: AsyncSession,
    sample_work_order,
    sample_employee,
    sample_activity_code,
):
    """Test that unique job cards don't trigger duplication."""
    jobcard = JobCard(
        employee_id=sample_employee.id,
        machine_id=sample_work_order.machine_id,
        work_order_id=sample_work_order.id,
        activity_code_id=sample_activity_code.id,
        activity_desc="Test work",
        qty=10.0,
        actual_hours=5.0,
        status=JobCardStatusEnum.C,
        entry_date=date(2024, 11, 5),
        source=SourceEnum.TECHNICIAN,
    )
    async_session.add(jobcard)
    await async_session.commit()
    await async_session.refresh(jobcard)
    
    flags = await duplication_rule(jobcard, async_session)
    
    assert len(flags) == 0


@pytest.mark.asyncio
async def test_duplication_rule_finds_duplicates(
    async_session: AsyncSession,
    sample_work_order,
    sample_employee,
    sample_activity_code,
):
    """Test that duplicate job cards are detected."""
    # Create first job card
    jobcard1 = JobCard(
        employee_id=sample_employee.id,
        machine_id=sample_work_order.machine_id,
        work_order_id=sample_work_order.id,
        activity_code_id=sample_activity_code.id,
        activity_desc="Test work",
        qty=10.0,
        actual_hours=5.0,
        status=JobCardStatusEnum.C,
        entry_date=date(2024, 11, 5),
        source=SourceEnum.TECHNICIAN,
    )
    async_session.add(jobcard1)
    await async_session.commit()
    await async_session.refresh(jobcard1)
    
    # Create duplicate job card (same machine, WO, activity)
    jobcard2 = JobCard(
        employee_id=sample_employee.id,
        machine_id=sample_work_order.machine_id,
        work_order_id=sample_work_order.id,
        activity_code_id=sample_activity_code.id,
        activity_desc="Test work duplicate",
        qty=15.0,
        actual_hours=7.0,
        status=JobCardStatusEnum.C,
        entry_date=date(2024, 11, 6),
        source=SourceEnum.TECHNICIAN,
    )
    async_session.add(jobcard2)
    await async_session.commit()
    await async_session.refresh(jobcard2)
    
    flags = await duplication_rule(jobcard2, async_session)
    
    assert len(flags) == 1
    assert flags[0].flag_type == FlagTypeEnum.DUPLICATION
    assert "duplicate" in flags[0].details.lower()
    assert str(jobcard1.id) in flags[0].details


# ============================================================================
# TEST: AWC Rule
# ============================================================================

@pytest.mark.asyncio
async def test_awc_rule_with_activity_code(
    async_session: AsyncSession,
    sample_work_order,
    sample_employee,
    sample_activity_code,
):
    """Test that job cards with activity code don't trigger AWC."""
    jobcard = JobCard(
        employee_id=sample_employee.id,
        machine_id=sample_work_order.machine_id,
        work_order_id=sample_work_order.id,
        activity_code_id=sample_activity_code.id,
        activity_desc="Test work",
        qty=10.0,
        actual_hours=5.0,
        status=JobCardStatusEnum.C,
        entry_date=date(2024, 11, 5),
        source=SourceEnum.TECHNICIAN,
    )
    async_session.add(jobcard)
    await async_session.commit()
    await async_session.refresh(jobcard)
    
    flags = await awc_rule(jobcard, async_session)
    
    assert len(flags) == 0


@pytest.mark.asyncio
async def test_awc_rule_without_activity_code(
    async_session: AsyncSession,
    sample_work_order,
    sample_employee,
):
    """Test that job cards without activity code trigger AWC."""
    jobcard = JobCard(
        employee_id=sample_employee.id,
        machine_id=sample_work_order.machine_id,
        work_order_id=sample_work_order.id,
        activity_code_id=None,  # No activity code
        activity_desc="Test work",
        qty=10.0,
        actual_hours=5.0,
        status=JobCardStatusEnum.C,
        entry_date=date(2024, 11, 5),
        source=SourceEnum.TECHNICIAN,
    )
    async_session.add(jobcard)
    await async_session.commit()
    await async_session.refresh(jobcard)
    
    flags = await awc_rule(jobcard, async_session)
    
    assert len(flags) == 1
    assert flags[0].flag_type == FlagTypeEnum.AWC
    assert "no activity_code_id" in flags[0].details


# ============================================================================
# TEST: Split Candidate Rule
# ============================================================================

@pytest.mark.asyncio
async def test_split_candidate_rule_no_split(
    async_session: AsyncSession,
    sample_work_order,
    sample_employee,
    sample_activity_code,
):
    """Test that single job cards don't trigger split candidate."""
    jobcard = JobCard(
        employee_id=sample_employee.id,
        machine_id=sample_work_order.machine_id,
        work_order_id=sample_work_order.id,
        activity_code_id=sample_activity_code.id,
        activity_desc="Test work",
        qty=10.0,
        actual_hours=5.0,
        status=JobCardStatusEnum.IC,
        entry_date=date(2024, 11, 5),
        source=SourceEnum.TECHNICIAN,
    )
    async_session.add(jobcard)
    await async_session.commit()
    await async_session.refresh(jobcard)
    
    flags = await split_candidate_rule(jobcard, async_session)
    
    assert len(flags) == 0


@pytest.mark.asyncio
async def test_split_candidate_rule_detects_split(
    async_session: AsyncSession,
    sample_work_order,
    sample_activity_code,
):
    """Test that split work between employees is detected."""
    # Create employee 1
    emp1 = EfficiencyEmployee(
        ec_number="EMP001",
        name="Employee 1",
        hashed_password="dummy",
        role=RoleEnum.OPERATOR,
        team="Team A",
        join_date=date.today(),
        is_active=True,
    )
    async_session.add(emp1)
    await async_session.commit()
    await async_session.refresh(emp1)
    
    # Create employee 2
    emp2 = EfficiencyEmployee(
        ec_number="EMP002",
        name="Employee 2",
        hashed_password="dummy",
        role=RoleEnum.OPERATOR,
        team="Team A",
        join_date=date.today(),
        is_active=True,
    )
    async_session.add(emp2)
    await async_session.commit()
    await async_session.refresh(emp2)
    
    # Employee 1 completes the work
    jobcard1 = JobCard(
        employee_id=emp1.id,
        machine_id=sample_work_order.machine_id,
        work_order_id=sample_work_order.id,
        activity_code_id=sample_activity_code.id,
        activity_desc="Completed work",
        qty=50.0,
        actual_hours=5.0,
        status=JobCardStatusEnum.C,  # Complete
        entry_date=date(2024, 11, 5),
        source=SourceEnum.TECHNICIAN,
    )
    async_session.add(jobcard1)
    await async_session.commit()
    await async_session.refresh(jobcard1)
    
    # Employee 2 has incomplete work on same WO/activity
    jobcard2 = JobCard(
        employee_id=emp2.id,
        machine_id=sample_work_order.machine_id,
        work_order_id=sample_work_order.id,
        activity_code_id=sample_activity_code.id,
        activity_desc="Incomplete work",
        qty=30.0,
        actual_hours=3.0,
        status=JobCardStatusEnum.IC,  # Incomplete
        entry_date=date(2024, 11, 6),
        source=SourceEnum.TECHNICIAN,
    )
    async_session.add(jobcard2)
    await async_session.commit()
    await async_session.refresh(jobcard2)
    
    flags = await split_candidate_rule(jobcard2, async_session)
    
    # Should flag both job cards
    assert len(flags) >= 2
    flagged_ids = {flag.job_card_id for flag in flags}
    assert jobcard1.id in flagged_ids
    assert jobcard2.id in flagged_ids
    assert all(flag.flag_type == FlagTypeEnum.SPLIT_CANDIDATE for flag in flags)


# ============================================================================
# TEST: Quantity Mismatch Rule
# ============================================================================

@pytest.mark.asyncio
async def test_qty_mismatch_rule_within_planned(
    async_session: AsyncSession,
    sample_work_order,
    sample_employee,
    sample_activity_code,
):
    """Test that quantities within planned don't trigger mismatch."""
    jobcard = JobCard(
        employee_id=sample_employee.id,
        machine_id=sample_work_order.machine_id,
        work_order_id=sample_work_order.id,
        activity_code_id=sample_activity_code.id,
        activity_desc="Test work",
        qty=50.0,  # Less than planned (100)
        actual_hours=5.0,
        status=JobCardStatusEnum.C,
        entry_date=date(2024, 11, 5),
        source=SourceEnum.TECHNICIAN,
    )
    async_session.add(jobcard)
    await async_session.commit()
    await async_session.refresh(jobcard)
    
    flags = await qty_mismatch_rule(jobcard, async_session)
    
    assert len(flags) == 0


@pytest.mark.asyncio
async def test_qty_mismatch_rule_exceeds_planned(
    async_session: AsyncSession,
    sample_work_order,
    sample_employee,
    sample_activity_code,
):
    """Test that single job card exceeding planned triggers mismatch."""
    jobcard = JobCard(
        employee_id=sample_employee.id,
        machine_id=sample_work_order.machine_id,
        work_order_id=sample_work_order.id,
        activity_code_id=sample_activity_code.id,
        activity_desc="Test work",
        qty=150.0,  # Exceeds planned (100)
        actual_hours=15.0,
        status=JobCardStatusEnum.C,
        entry_date=date(2024, 11, 5),
        source=SourceEnum.TECHNICIAN,
    )
    async_session.add(jobcard)
    await async_session.commit()
    await async_session.refresh(jobcard)
    
    flags = await qty_mismatch_rule(jobcard, async_session)
    
    assert len(flags) >= 1
    assert any(flag.flag_type == FlagTypeEnum.QTY_MISMATCH for flag in flags)
    assert any("150" in flag.details for flag in flags)


@pytest.mark.asyncio
async def test_qty_mismatch_rule_total_exceeds_tolerance(
    async_session: AsyncSession,
    sample_work_order,
    sample_employee,
    sample_activity_code,
):
    """Test that total quantities exceeding 10% tolerance triggers mismatch."""
    # Create multiple job cards that together exceed 110% of planned
    jobcard1 = JobCard(
        employee_id=sample_employee.id,
        machine_id=sample_work_order.machine_id,
        work_order_id=sample_work_order.id,
        activity_code_id=sample_activity_code.id,
        activity_desc="Work 1",
        qty=70.0,
        actual_hours=7.0,
        status=JobCardStatusEnum.C,
        entry_date=date(2024, 11, 5),
        source=SourceEnum.TECHNICIAN,
    )
    async_session.add(jobcard1)
    await async_session.commit()
    
    jobcard2 = JobCard(
        employee_id=sample_employee.id,
        machine_id=sample_work_order.machine_id,
        work_order_id=sample_work_order.id,
        activity_code_id=sample_activity_code.id,
        activity_desc="Work 2",
        qty=50.0,  # Total = 120, exceeds 110
        actual_hours=5.0,
        status=JobCardStatusEnum.C,
        entry_date=date(2024, 11, 6),
        source=SourceEnum.TECHNICIAN,
    )
    async_session.add(jobcard2)
    await async_session.commit()
    await async_session.refresh(jobcard2)
    
    flags = await qty_mismatch_rule(jobcard2, async_session)
    
    assert len(flags) >= 1
    assert any(flag.flag_type == FlagTypeEnum.QTY_MISMATCH for flag in flags)
    assert any("120" in flag.details or "total" in flag.details.lower() for flag in flags)


# ============================================================================
# TEST: ValidationEngine Class
# ============================================================================

@pytest.mark.asyncio
async def test_validation_engine_integration(
    async_session: AsyncSession,
    sample_work_order,
    sample_employee,
):
    """Test that ValidationEngine runs all rules and creates flags."""
    # Create job card with multiple issues:
    # 1. Outside MSD window
    # 2. No activity code (AWC)
    jobcard = JobCard(
        employee_id=sample_employee.id,
        machine_id=sample_work_order.machine_id,
        work_order_id=sample_work_order.id,
        activity_code_id=None,  # AWC
        activity_desc="Test work",
        qty=10.0,
        actual_hours=5.0,
        status=JobCardStatusEnum.C,
        entry_date=date(2024, 11, 20),  # Outside window
        source=SourceEnum.TECHNICIAN,
    )
    async_session.add(jobcard)
    await async_session.commit()
    await async_session.refresh(jobcard)
    
    engine = ValidationEngine()
    flags = await engine.run_for_jobcard(jobcard, async_session)
    
    # Should have at least 2 flags (OUTSIDE_MSD and AWC)
    assert len(flags) >= 2
    flag_types = {flag.flag_type for flag in flags}
    assert FlagTypeEnum.OUTSIDE_MSD in flag_types
    assert FlagTypeEnum.AWC in flag_types


@pytest.mark.asyncio
async def test_validation_engine_idempotence(
    async_session: AsyncSession,
    sample_work_order,
    sample_employee,
):
    """Test that running validation twice doesn't create duplicate flags."""
    jobcard = JobCard(
        employee_id=sample_employee.id,
        machine_id=sample_work_order.machine_id,
        work_order_id=sample_work_order.id,
        activity_code_id=None,  # AWC
        activity_desc="Test work",
        qty=10.0,
        actual_hours=5.0,
        status=JobCardStatusEnum.C,
        entry_date=date(2024, 11, 5),
        source=SourceEnum.TECHNICIAN,
    )
    async_session.add(jobcard)
    await async_session.commit()
    await async_session.refresh(jobcard)
    
    engine = ValidationEngine()
    
    # Run validation first time
    flags1 = await engine.run_for_jobcard(jobcard, async_session)
    first_count = len(flags1)
    
    # Run validation second time
    flags2 = await engine.run_for_jobcard(jobcard, async_session)
    second_count = len(flags2)
    
    # Should have same number of flags (idempotent)
    assert first_count == second_count
    
    # Check database has no duplicate flags
    statement = select(ValidationFlag).where(
        ValidationFlag.job_card_id == jobcard.id,
        ValidationFlag.resolved == False,
    )
    result = await async_session.execute(statement)
    db_flags = result.scalars().all()
    
    assert len(db_flags) == first_count, "Database should not have duplicate flags"
