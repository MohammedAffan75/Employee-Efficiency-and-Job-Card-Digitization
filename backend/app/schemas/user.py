from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    username: str


class UserCreate(UserBase):
    """Schema for creating a user."""
    password: str


class UserRead(UserBase):
    """Schema for reading user data."""
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime


class UserUpdate(BaseModel):
    """Schema for updating user data."""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None
