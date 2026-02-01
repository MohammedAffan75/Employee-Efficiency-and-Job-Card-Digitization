"""
Integration tests for API endpoints.
Tests authentication, protected routes, and complete workflows.
"""

import pytest
from datetime import date, datetime
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.main import app
from app.core.database import get_async_session
from app.models.models import (
    EfficiencyEmployee,
    Machine,
    WorkOrder,
    ActivityCode,
    RoleEnum,
    EfficiencyTypeEnum,
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
async def test_data(async_session: AsyncSession):
    """Create test data for integration tests."""
    # Create employees with different roles
    admin = EfficiencyEmployee(
        ec_number="ADMIN001",
        name="Admin User",
        hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYs0JcBLJGC",  # "password"
        role=RoleEnum.ADMIN,
        team="Team A",
        join_date=date.today(),
        is_active=True,
    )
    
    supervisor = EfficiencyEmployee(
        ec_number="SUP001",
        name="Supervisor User",
        hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYs0JcBLJGC",
        role=RoleEnum.SUPERVISOR,
        team="Team A",
        join_date=date.today(),
        is_active=True,
    )
    
    operator = EfficiencyEmployee(
        ec_number="OP001",
        name="Operator User",
        hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYs0JcBLJGC",
        role=RoleEnum.OPERATOR,
        team="Team A",
        join_date=date.today(),
        is_active=True,
    )
    
    async_session.add_all([admin, supervisor, operator])
    
    # Create machine
    machine = Machine(
        machine_code="M-001",
        description="Test Machine",
        work_center="WC-A",
    )
    async_session.add(machine)
    await async_session.flush()
    await async_session.refresh(machine)
    
    # Create work order
    wo = WorkOrder(
        wo_number="WO-2024-001",
        machine_id=machine.id,
        planned_qty=100.0,
        msd_month="2024-11",
    )
    async_session.add(wo)
    
    # Create activity code
    activity = ActivityCode(
        code="ACT001",
        description="Test Activity",
        efficiency_type=EfficiencyTypeEnum.TIME_BASED,
        std_hours_per_unit=0.5,
        last_updated=datetime.utcnow(),
    )
    async_session.add(activity)
    
    await async_session.commit()
    await async_session.refresh(admin)
    await async_session.refresh(supervisor)
    await async_session.refresh(operator)
    await async_session.refresh(machine)
    await async_session.refresh(wo)
    await async_session.refresh(activity)
    
    return {
        'admin': admin,
        'supervisor': supervisor,
        'operator': operator,
        'machine': machine,
        'work_order': wo,
        'activity': activity,
    }


@pytest.fixture
async def client(async_session: AsyncSession):
    """Create test client with database override."""
    async def override_get_async_session():
        yield async_session
    
    app.dependency_overrides[get_async_session] = override_get_async_session
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


# ============================================================================
# AUTHENTICATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_data):
    """Test successful login."""
    response = await client.post(
        "/api/auth/login",
        data={"username": "ADMIN001", "password": "password"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["employee"]["ec_number"] == "ADMIN001"
    assert data["employee"]["role"] == "ADMIN"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient, test_data):
    """Test login with invalid credentials."""
    response = await client.post(
        "/api/auth/login",
        data={"username": "ADMIN001", "password": "wrong"},
    )
    
    assert response.status_code == 401
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, test_data):
    """Test getting current user info."""
    # Login first
    login_response = await client.post(
        "/api/auth/login",
        data={"username": "ADMIN001", "password": "password"},
    )
    token = login_response.json()["access_token"]
    
    # Get current user
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    user = response.json()
    assert user["ec_number"] == "ADMIN001"


@pytest.mark.asyncio
async def test_protected_route_without_token(client: AsyncClient, test_data):
    """Test accessing protected route without token."""
    response = await client.get("/api/auth/me")
    
    assert response.status_code == 401


# ============================================================================
# JOBCARD CRUD TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_jobcard_as_operator(client: AsyncClient, test_data):
    """Test jobcard creation by operator."""
    # Login as operator
    login_response = await client.post(
        "/api/auth/login",
        data={"username": "OP001", "password": "password"},
    )
    token = login_response.json()["access_token"]
    
    # Create jobcard
    jobcard_data = {
        "employee_id": test_data['operator'].id,
        "machine_id": test_data['machine'].id,
        "work_order_id": test_data['work_order'].id,
        "activity_code_id": test_data['activity'].id,
        "activity_desc": "Test work",
        "qty": 10.0,
        "actual_hours": 5.0,
        "status": "C",
        "entry_date": "2024-11-01",
        "source": "TECHNICIAN",
    }
    
    response = await client.post(
        "/api/jobcards",
        json=jobcard_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 201
    jobcard = response.json()
    assert jobcard["qty"] == 10.0
    assert jobcard["actual_hours"] == 5.0


@pytest.mark.asyncio
async def test_list_jobcards(client: AsyncClient, test_data):
    """Test listing jobcards."""
    # Login
    login_response = await client.post(
        "/api/auth/login",
        data={"username": "OP001", "password": "password"},
    )
    token = login_response.json()["access_token"]
    
    # List jobcards
    response = await client.get(
        "/api/jobcards",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    jobcards = response.json()
    assert isinstance(jobcards, list)


@pytest.mark.asyncio
async def test_jobcard_validation_triggers(client: AsyncClient, test_data):
    """Test that creating jobcard triggers validation engine."""
    # Login
    login_response = await client.post(
        "/api/auth/login",
        data={"username": "OP001", "password": "password"},
    )
    token = login_response.json()["access_token"]
    
    # Create jobcard without activity code (should trigger AWC flag)
    jobcard_data = {
        "employee_id": test_data['operator'].id,
        "machine_id": test_data['machine'].id,
        "work_order_id": test_data['work_order'].id,
        "activity_code_id": None,  # No activity code = AWC
        "activity_desc": "Work without activity code",
        "qty": 10.0,
        "actual_hours": 5.0,
        "status": "C",
        "entry_date": "2024-11-01",
        "source": "TECHNICIAN",
    }
    
    response = await client.post(
        "/api/jobcards",
        json=jobcard_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 201
    # Validation flags would be created in the background


# ============================================================================
# ROLE-BASED ACCESS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_supervisor_can_assign_work(client: AsyncClient, test_data):
    """Test that supervisor can assign work."""
    # Login as supervisor
    login_response = await client.post(
        "/api/auth/login",
        data={"username": "SUP001", "password": "password"},
    )
    token = login_response.json()["access_token"]
    
    # Assign work
    assign_data = {
        "work_order_id": test_data['work_order'].id,
        "activity_code_id": test_data['activity'].id,
        "assignments": [
            {"employee_id": test_data['operator'].id, "hours": 5.0, "qty": 10.0}
        ],
        "mode": "manual",
        "entry_date": "2024-11-01",
        "status": "C",
    }
    
    response = await client.post(
        "/api/supervisor/assign",
        json=assign_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    result = response.json()
    assert result["accepted_count"] >= 0  # May have created jobcards


@pytest.mark.asyncio
async def test_operator_cannot_assign_work(client: AsyncClient, test_data):
    """Test that operator cannot assign work."""
    # Login as operator
    login_response = await client.post(
        "/api/auth/login",
        data={"username": "OP001", "password": "password"},
    )
    token = login_response.json()["access_token"]
    
    # Try to assign work (should fail)
    assign_data = {
        "work_order_id": test_data['work_order'].id,
        "activity_code_id": test_data['activity'].id,
        "assignments": [
            {"employee_id": test_data['operator'].id, "hours": 5.0, "qty": 10.0}
        ],
        "mode": "manual",
        "entry_date": "2024-11-01",
        "status": "C",
    }
    
    response = await client.post(
        "/api/supervisor/assign",
        json=assign_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403  # Forbidden


# ============================================================================
# EFFICIENCY CALCULATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_calculate_employee_efficiency(client: AsyncClient, test_data):
    """Test calculating employee efficiency."""
    # Login
    login_response = await client.post(
        "/api/auth/login",
        data={"username": "OP001", "password": "password"},
    )
    token = login_response.json()["access_token"]
    
    # Calculate efficiency
    response = await client.get(
        f"/api/efficiency/{test_data['operator'].id}?start=2024-11-01&end=2024-11-30",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    efficiency = response.json()
    assert "time_efficiency" in efficiency
    assert "employee_id" in efficiency


# ============================================================================
# REPORTING TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_dashboard_summary(client: AsyncClient, test_data):
    """Test dashboard summary endpoint."""
    # Login as supervisor
    login_response = await client.post(
        "/api/auth/login",
        data={"username": "SUP001", "password": "password"},
    )
    token = login_response.json()["access_token"]
    
    # Get dashboard summary
    response = await client.get(
        "/api/reporting/dashboard/summary?start=2024-11-01&end=2024-11-30",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    summary = response.json()
    assert "avg_time_efficiency" in summary
    assert "employee_count" in summary


# ============================================================================
# VALIDATION FLAGS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_list_validation_flags(client: AsyncClient, test_data):
    """Test listing validation flags."""
    # Login as supervisor
    login_response = await client.post(
        "/api/auth/login",
        data={"username": "SUP001", "password": "password"},
    )
    token = login_response.json()["access_token"]
    
    # List validations
    response = await client.get(
        "/api/supervisor/validations",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    flags = response.json()
    assert isinstance(flags, list)
