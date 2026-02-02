"""
Authentication schemas.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from app.schemas.base import BaseSchema


class LoginRequest(BaseModel):
    """Login request with credentials."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str


class RefreshResponse(BaseModel):
    """Token refresh response."""
    access_token: str
    token_type: str = "bearer"


class RegisterCompanyRequest(BaseModel):
    """Registration request for new company + admin user."""
    # Company data
    company_code: str = Field(..., min_length=3, max_length=20)
    company_name: str = Field(..., min_length=2, max_length=200)
    company_tax_id: Optional[str] = Field(None, max_length=20)

    # Admin user data
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)


class UserResponse(BaseSchema):
    """User data response (safe, no password)."""
    id: UUID
    company_id: UUID
    username: str
    email: str
    full_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str
    is_active: bool


class LoginResponse(BaseModel):
    """Complete login response with tokens and user."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
