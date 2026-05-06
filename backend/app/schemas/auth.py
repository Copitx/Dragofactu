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
    password: str = Field(..., min_length=8, max_length=128)


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


class LogoutRequest(BaseModel):
    """Optional logout payload to revoke refresh token as well."""
    refresh_token: Optional[str] = None


class RegisterCompanyRequest(BaseModel):
    """Registration request for new company + admin user."""
    # Company data
    company_code: str = Field(..., min_length=3, max_length=20)
    company_name: str = Field(..., min_length=2, max_length=200)
    company_tax_id: Optional[str] = Field(None, max_length=20)

    # Admin user data
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)


class CreateUserRequest(BaseModel):
    """Request for admin to create a new user in their company."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=100)
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    role: str = Field(default="read_only")


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
    is_superadmin: bool = False
    company_name: Optional[str] = None


class LoginResponse(BaseModel):
    """Complete login response with tokens and user."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
