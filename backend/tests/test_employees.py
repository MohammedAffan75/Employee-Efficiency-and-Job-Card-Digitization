import pytest
from fastapi.testclient import TestClient


def get_auth_token(client: TestClient) -> str:
    """Helper function to register and login a user."""
    client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpassword123"
        }
    )
    login_response = client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "testpassword123"}
    )
    return login_response.json()["access_token"]


def test_create_employee(client: TestClient):
    """Test creating an employee."""
    token = get_auth_token(client)
    
    response = client.post(
        "/api/employees/",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "department": "Engineering",
            "position": "Software Engineer",
            "salary": 75000.00
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["first_name"] == "John"
    assert data["last_name"] == "Doe"
    assert data["email"] == "john.doe@example.com"
    assert "id" in data


def test_get_employees(client: TestClient):
    """Test getting all employees."""
    token = get_auth_token(client)
    
    # Create an employee first
    client.post(
        "/api/employees/",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "department": "Engineering",
            "position": "Software Engineer",
            "salary": 75000.00
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    response = client.get(
        "/api/employees/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_employee_by_id(client: TestClient):
    """Test getting a single employee by ID."""
    token = get_auth_token(client)
    
    # Create an employee
    create_response = client.post(
        "/api/employees/",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "department": "Engineering",
            "position": "Software Engineer",
            "salary": 75000.00
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    employee_id = create_response.json()["id"]
    
    # Get the employee
    response = client.get(
        f"/api/employees/{employee_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == employee_id
    assert data["first_name"] == "John"


def test_update_employee(client: TestClient):
    """Test updating an employee."""
    token = get_auth_token(client)
    
    # Create an employee
    create_response = client.post(
        "/api/employees/",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "department": "Engineering",
            "position": "Software Engineer",
            "salary": 75000.00
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    employee_id = create_response.json()["id"]
    
    # Update the employee
    response = client.patch(
        f"/api/employees/{employee_id}",
        json={"salary": 85000.00, "position": "Senior Software Engineer"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["salary"] == 85000.00
    assert data["position"] == "Senior Software Engineer"


def test_delete_employee(client: TestClient):
    """Test deleting an employee."""
    token = get_auth_token(client)
    
    # Create an employee
    create_response = client.post(
        "/api/employees/",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "department": "Engineering",
            "position": "Software Engineer",
            "salary": 75000.00
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    employee_id = create_response.json()["id"]
    
    # Delete the employee
    response = client.delete(
        f"/api/employees/{employee_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 204
    
    # Verify it's deleted
    response = client.get(
        f"/api/employees/{employee_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


def test_unauthorized_access(client: TestClient):
    """Test that endpoints require authentication."""
    response = client.get("/api/employees/")
    assert response.status_code == 401
