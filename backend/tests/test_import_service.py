"""
Unit tests for import_service - testing mapping edge cases and validation.
"""

import pytest
import io
from datetime import date

import pandas as pd
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.models.models import (
    EfficiencyEmployee,
    Machine,
    WorkOrder,
    ActivityCode,
    RoleEnum,
    EfficiencyTypeEnum,
)
from app.services.import_service import (
    import_jobcards_from_file,
    _parse_file,
    _validate_and_map_row,
)


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
async def async_session():
    """Create async test database session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session
    await engine.dispose()


@pytest.fixture
async def sample_data(async_session: AsyncSession):
    """Create sample employees, machines, work orders, and activity codes."""
    # Employee
    emp = EfficiencyEmployee(
        ec_number="EC001",
        name="John Doe",
        hashed_password="dummy",
        role=RoleEnum.OPERATOR,
        team="Team A",
        join_date=date.today(),
        is_active=True,
    )
    async_session.add(emp)
    
    # Machine
    machine = Machine(
        machine_code="M001",
        description="Test Machine",
        work_center="WC-A",
    )
    async_session.add(machine)
    await async_session.flush()
    await async_session.refresh(machine)
    
    # Work Order
    wo = WorkOrder(
        wo_number="WO-2024-001",
        machine_id=machine.id,
        planned_qty=100.0,
        msd_month="2024-11",
    )
    async_session.add(wo)
    
    # Activity Code
    activity = ActivityCode(
        code="ACT001",
        description="Test Activity",
        efficiency_type=EfficiencyTypeEnum.TIME_BASED,
        std_hours_per_unit=0.5,
        last_updated=date.today(),
    )
    async_session.add(activity)
    
    await async_session.commit()
    await async_session.refresh(emp)
    await async_session.refresh(machine)
    await async_session.refresh(wo)
    await async_session.refresh(activity)
    
    return {
        'employee': emp,
        'machine': machine,
        'work_order': wo,
        'activity': activity,
    }


# ============================================================================
# TEST FILE PARSING
# ============================================================================

@pytest.mark.asyncio
async def test_parse_csv_file():
    """Test parsing CSV file."""
    csv_content = b"""ec_number,entry_date,machine_code,wo_number,activity_code,activity_desc,qty,actual_hours,status
EC001,2024-11-01,M001,WO-001,ACT001,Test work,10.0,5.0,C
"""
    df = _parse_file(csv_content, "test.csv")
    assert len(df) == 1
    assert 'ec_number' in df.columns
    assert df.iloc[0]['ec_number'] == 'EC001'


@pytest.mark.asyncio
async def test_parse_excel_file():
    """Test parsing Excel file."""
    # Create test Excel file in memory
    df = pd.DataFrame({
        'ec_number': ['EC001'],
        'entry_date': ['2024-11-01'],
        'machine_code': ['M001'],
        'wo_number': ['WO-001'],
        'activity_code': ['ACT001'],
        'activity_desc': ['Test work'],
        'qty': [10.0],
        'actual_hours': [5.0],
        'status': ['C'],
    })
    
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, engine='openpyxl')
    excel_content = buffer.getvalue()
    
    parsed_df = _parse_file(excel_content, "test.xlsx")
    assert len(parsed_df) == 1
    assert parsed_df.iloc[0]['ec_number'] == 'EC001'


@pytest.mark.asyncio
async def test_parse_unsupported_file():
    """Test that unsupported file types raise error."""
    with pytest.raises(ValueError, match="Unsupported file type"):
        _parse_file(b"dummy", "test.txt")


# ============================================================================
# TEST ROW VALIDATION
# ============================================================================

@pytest.mark.asyncio
async def test_validate_row_success():
    """Test successful row validation."""
    row_data = {
        'ec_number': 'EC001',
        'entry_date': '2024-11-01',
        'machine_code': 'M001',
        'wo_number': 'WO-001',
        'activity_code': 'ACT001',
        'activity_desc': 'Test work',
        'qty': 10.0,
        'actual_hours': 5.0,
        'status': 'C',
    }
    
    employees_map = {'EC001': 1}
    machines_map = {'M001': 1}
    work_orders_map = {'WO-001': 1}
    activity_codes_map = {'ACT001': 1}
    
    jobcard_data, error = await _validate_and_map_row(
        row_data, 1, employees_map, machines_map, work_orders_map, activity_codes_map
    )
    
    assert error is None
    assert jobcard_data['employee_id'] == 1
    assert jobcard_data['machine_id'] == 1
    assert jobcard_data['work_order_id'] == 1
    assert jobcard_data['activity_code_id'] == 1
    assert jobcard_data['qty'] == 10.0
    assert jobcard_data['actual_hours'] == 5.0


@pytest.mark.asyncio
async def test_validate_row_missing_employee():
    """Test row validation with missing employee."""
    row_data = {
        'ec_number': 'EC999',  # Not in map
        'entry_date': '2024-11-01',
        'machine_code': 'M001',
        'wo_number': 'WO-001',
        'activity_code': 'ACT001',
        'activity_desc': 'Test work',
        'qty': 10.0,
        'actual_hours': 5.0,
        'status': 'C',
    }
    
    employees_map = {'EC001': 1}
    machines_map = {'M001': 1}
    work_orders_map = {'WO-001': 1}
    activity_codes_map = {'ACT001': 1}
    
    jobcard_data, error = await _validate_and_map_row(
        row_data, 1, employees_map, machines_map, work_orders_map, activity_codes_map
    )
    
    assert error is not None
    assert "Employee not found" in error


@pytest.mark.asyncio
async def test_validate_row_missing_machine():
    """Test row validation with missing machine."""
    row_data = {
        'ec_number': 'EC001',
        'entry_date': '2024-11-01',
        'machine_code': 'M999',  # Not in map
        'wo_number': 'WO-001',
        'activity_code': 'ACT001',
        'activity_desc': 'Test work',
        'qty': 10.0,
        'actual_hours': 5.0,
        'status': 'C',
    }
    
    employees_map = {'EC001': 1}
    machines_map = {'M001': 1}
    work_orders_map = {'WO-001': 1}
    activity_codes_map = {'ACT001': 1}
    
    jobcard_data, error = await _validate_and_map_row(
        row_data, 1, employees_map, machines_map, work_orders_map, activity_codes_map
    )
    
    assert error is not None
    assert "Machine not found" in error


@pytest.mark.asyncio
async def test_validate_row_awc_case():
    """Test AWC case (activity code empty/null)."""
    row_data = {
        'ec_number': 'EC001',
        'entry_date': '2024-11-01',
        'machine_code': 'M001',
        'wo_number': 'WO-001',
        'activity_code': '',  # Empty - AWC case
        'activity_desc': 'Work without activity code',
        'qty': 10.0,
        'actual_hours': 5.0,
        'status': 'C',
    }
    
    employees_map = {'EC001': 1}
    machines_map = {'M001': 1}
    work_orders_map = {'WO-001': 1}
    activity_codes_map = {'ACT001': 1}
    
    jobcard_data, error = await _validate_and_map_row(
        row_data, 1, employees_map, machines_map, work_orders_map, activity_codes_map
    )
    
    assert error is None
    assert jobcard_data['activity_code_id'] is None  # AWC case


@pytest.mark.asyncio
async def test_validate_row_invalid_status():
    """Test row validation with invalid status."""
    row_data = {
        'ec_number': 'EC001',
        'entry_date': '2024-11-01',
        'machine_code': 'M001',
        'wo_number': 'WO-001',
        'activity_code': 'ACT001',
        'activity_desc': 'Test work',
        'qty': 10.0,
        'actual_hours': 5.0,
        'status': 'INVALID',  # Invalid status
    }
    
    employees_map = {'EC001': 1}
    machines_map = {'M001': 1}
    work_orders_map = {'WO-001': 1}
    activity_codes_map = {'ACT001': 1}
    
    jobcard_data, error = await _validate_and_map_row(
        row_data, 1, employees_map, machines_map, work_orders_map, activity_codes_map
    )
    
    assert error is not None
    assert "Invalid status" in error


@pytest.mark.asyncio
async def test_validate_row_date_formats():
    """Test different date formats."""
    # Test YYYY-MM-DD format
    row_data = {
        'ec_number': 'EC001',
        'entry_date': '2024-11-01',
        'machine_code': 'M001',
        'wo_number': 'WO-001',
        'activity_code': 'ACT001',
        'activity_desc': 'Test',
        'qty': 10.0,
        'actual_hours': 5.0,
        'status': 'C',
    }
    
    maps = ({'EC001': 1}, {'M001': 1}, {'WO-001': 1}, {'ACT001': 1})
    jobcard_data, error = await _validate_and_map_row(row_data, 1, *maps)
    assert error is None
    assert jobcard_data['entry_date'] == date(2024, 11, 1)
    
    # Test DD/MM/YYYY format
    row_data['entry_date'] = '01/11/2024'
    jobcard_data, error = await _validate_and_map_row(row_data, 1, *maps)
    assert error is None
    assert jobcard_data['entry_date'] == date(2024, 11, 1)


# ============================================================================
# TEST FULL IMPORT
# ============================================================================

@pytest.mark.asyncio
async def test_import_jobcards_success(async_session: AsyncSession, sample_data):
    """Test successful import of jobcards."""
    # Create CSV content
    csv_content = b"""ec_number,entry_date,machine_code,wo_number,activity_code,activity_desc,qty,actual_hours,status
EC001,2024-11-01,M001,WO-2024-001,ACT001,Test work,10.0,5.0,C
EC001,2024-11-02,M001,WO-2024-001,ACT001,More work,15.0,8.0,C
"""
    
    report = await import_jobcards_from_file(
        file_content=csv_content,
        filename="test.csv",
        supervisor_id=sample_data['employee'].id,
        session=async_session,
    )
    
    assert report.total_rows == 2
    assert report.accepted_count == 2
    assert report.rejected_count == 0


@pytest.mark.asyncio
async def test_import_jobcards_with_rejections(async_session: AsyncSession, sample_data):
    """Test import with some rejected rows."""
    csv_content = b"""ec_number,entry_date,machine_code,wo_number,activity_code,activity_desc,qty,actual_hours,status
EC001,2024-11-01,M001,WO-2024-001,ACT001,Valid work,10.0,5.0,C
EC999,2024-11-01,M001,WO-2024-001,ACT001,Invalid employee,10.0,5.0,C
EC001,2024-11-01,M999,WO-2024-001,ACT001,Invalid machine,10.0,5.0,C
"""
    
    report = await import_jobcards_from_file(
        file_content=csv_content,
        filename="test.csv",
        supervisor_id=sample_data['employee'].id,
        session=async_session,
    )
    
    assert report.total_rows == 3
    assert report.accepted_count == 1
    assert report.rejected_count == 2
    assert len(report.rejected) == 2
    assert "Employee not found" in report.rejected[0].reason or "Employee not found" in report.rejected[1].reason


@pytest.mark.asyncio
async def test_import_jobcards_awc_case(async_session: AsyncSession, sample_data):
    """Test import with AWC (no activity code) case."""
    csv_content = b"""ec_number,entry_date,machine_code,wo_number,activity_code,activity_desc,qty,actual_hours,status
EC001,2024-11-01,M001,WO-2024-001,,Work without code,10.0,5.0,C
"""
    
    report = await import_jobcards_from_file(
        file_content=csv_content,
        filename="test.csv",
        supervisor_id=sample_data['employee'].id,
        session=async_session,
    )
    
    assert report.total_rows == 1
    assert report.accepted_count == 1
    assert report.flagged_count >= 1  # Should be flagged as AWC
    assert any('AWC' in flag.flags for flag in report.flagged)
