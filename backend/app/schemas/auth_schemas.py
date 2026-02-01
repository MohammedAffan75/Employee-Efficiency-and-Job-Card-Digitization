"""
Authentication schemas for API requests and responses.
"""

from __future__ import annotations
from pydantic import BaseModel, Field


class AuthIn(BaseModel):
    """Login request schema."""
    
    ec_number: str = Field(..., description="Employee code number")
    password: str = Field(..., min_length=4, description="Employee password")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ec_number": "EMP001",
                    "password": "password123"
                }
            ]
        }
    }


class EmployeeInfo(BaseModel):
    """Current employee information."""
    
    id: int
    ec_number: str
    name: str
    role: str
    is_active: bool
    supervisor_efficiency_module: str | None = None
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "ec_number": "EMP001",
                    "name": "John Admin",
                    "role": "ADMIN",
                    "is_active": True
                }
            ]
        }
    }


class TokenOut(BaseModel):
    """Token response schema with employee info."""
    
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    employee: EmployeeInfo = Field(..., description="Employee information")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 3600,
                    "employee": {
                        "id": 1,
                        "ec_number": "EMP001",
                        "name": "John Doe",
                        "role": "OPERATOR",
                        "is_active": True
                    }
                }
            ]
        }
    }
