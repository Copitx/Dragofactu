"""
Company model - The tenant in multi-tenant architecture.
Each company has isolated data from other companies.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base
import uuid


class Company(Base):
    """
    Represents a company/tenant in the multi-tenant system.
    All other entities will have a company_id foreign key.
    """
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Identification
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    legal_name = Column(String(200))  # Razon social
    tax_id = Column(String(20))  # CIF/NIF

    # Contact
    address = Column(Text)
    city = Column(String(100))
    postal_code = Column(String(10))
    province = Column(String(100))
    country = Column(String(100), default='Espana')
    phone = Column(String(20))
    email = Column(String(100))
    website = Column(String(200))

    # Configuration
    logo_path = Column(String(500))  # URL or path to logo
    default_language = Column(String(5), default='es')
    default_currency = Column(String(3), default='EUR')
    tax_rate = Column(Float, default=21.0)  # Default IVA

    # Subscription/Plan (for future use)
    plan_type = Column(String(20), default='free')  # free, basic, pro
    max_users = Column(Integer, default=5)
    max_documents_month = Column(Integer, default=100)
    is_active = Column(Boolean, default=True)
    subscription_expires = Column(DateTime(timezone=True))

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships (will be added as we create other models)
    # users = relationship("User", back_populates="company")
    # clients = relationship("Client", back_populates="company")
    # products = relationship("Product", back_populates="company")
    # documents = relationship("Document", back_populates="company")

    def __repr__(self):
        return f"<Company {self.code}: {self.name}>"
