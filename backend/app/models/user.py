"""
User model with multi-tenant support.
Each user belongs to exactly one company.
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base, GUID
import enum
import uuid


class UserRole(str, enum.Enum):
    """User roles for RBAC."""
    ADMIN = "admin"
    MANAGEMENT = "management"
    WAREHOUSE = "warehouse"
    READ_ONLY = "read_only"


class User(Base):
    """
    User model with company association.
    Username is unique per company, not globally.
    """
    __tablename__ = "users"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Company association (tenant)
    company_id = Column(GUID(), ForeignKey("companies.id"), nullable=False, index=True)

    # Authentication
    username = Column(String(50), nullable=False, index=True)
    email = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)

    # Profile
    full_name = Column(String(100), nullable=False)
    first_name = Column(String(50))
    last_name = Column(String(50))

    # Authorization
    role = Column(Enum(UserRole), nullable=False, default=UserRole.READ_ONLY)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))

    # Relationships
    company = relationship("Company", back_populates="users")

    # Unique constraint: username unique per company
    __table_args__ = (
        UniqueConstraint('company_id', 'username', name='uq_user_company_username'),
        UniqueConstraint('company_id', 'email', name='uq_user_company_email'),
    )

    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission based on role."""
        role_permissions = {
            UserRole.ADMIN: ['*'],  # All permissions
            UserRole.MANAGEMENT: [
                'clients.*', 'products.*', 'documents.*',
                'inventory.*', 'workers.*', 'diary.*', 'reminders.*'
            ],
            UserRole.WAREHOUSE: [
                'products.read', 'inventory.*', 'documents.read'
            ],
            UserRole.READ_ONLY: [
                'clients.read', 'products.read', 'documents.read',
                'inventory.read', 'workers.read', 'diary.read'
            ]
        }

        user_perms = role_permissions.get(self.role, [])

        # Admin has all permissions
        if '*' in user_perms:
            return True

        # Check exact match or wildcard
        resource = permission.split('.')[0]
        for perm in user_perms:
            if perm == permission or perm == f'{resource}.*':
                return True

        return False

    def __repr__(self):
        return f"<User {self.username} ({self.role.value})>"
