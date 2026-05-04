"""
Authentication and Authorization Models
"""

from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional


class UserRole(str, Enum):
    """User roles in the system"""
    CHECKER = "checker"
    ACCOUNT_HOLDER = "account_holder"
    STAFF = "staff"
    ADMIN = "admin"


class LoginRequest(BaseModel):
    """Login credentials"""
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)


class LoginResponse(BaseModel):
    """Login response"""
    success: bool
    token: str
    user_id: str
    username: str
    role: UserRole
    customer_id: Optional[str] = None  # For account holders


class User(BaseModel):
    """User model"""
    user_id: str
    username: str
    role: UserRole
    customer_id: Optional[str] = None  # For account holders
    full_name: Optional[str] = None
    email: Optional[str] = None
    active: bool = True


class ChangePasswordRequest(BaseModel):
    """Change password request"""
    old_password: str
    new_password: str = Field(..., min_length=6)


class AccountDetailsResponse(BaseModel):
    """Account details response"""
    customer_id: str
    name: str
    email: str
    address: str
    dob: str
    phone: Optional[str] = None
    balance: Optional[float] = None  # Only visible to account holder
    account_number: Optional[str] = None
    account_type: Optional[str] = None
