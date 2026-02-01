from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime


class User(SQLModel, table=True):
    """User model for authentication and user management."""
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    username: str = Field(unique=True, index=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Employee(SQLModel, table=True):
    """Employee model for storing employee information."""
    id: Optional[int] = Field(default=None, primary_key=True)
    first_name: str
    last_name: str
    email: str = Field(unique=True, index=True)
    department: str
    position: str
    salary: float
    hire_date: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
