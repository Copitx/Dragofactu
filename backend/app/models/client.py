"""
Client model with multi-tenant support.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, Float, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base, GUID
import uuid


class Client(Base):
    """
    Client model - customers who receive invoices.
    Code is unique per company.
    """
    __tablename__ = "clients"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Company association (tenant)
    company_id = Column(GUID(), ForeignKey("companies.id"), nullable=False, index=True)

    # Identification
    code = Column(String(20), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    tax_id = Column(String(50))  # CIF/NIF

    # Address
    address = Column(Text)
    city = Column(String(100))
    postal_code = Column(String(20))
    province = Column(String(100))
    country = Column(String(100), default="Espana")

    # Contact
    phone = Column(String(50))
    email = Column(String(100))
    website = Column(String(200))

    # Additional
    notes = Column(Text)

    # Business fields
    payment_method = Column(String(50))     # "Transferencia", "Efectivo", "Tarjeta", "Domiciliacion"
    payment_days = Column(Integer, default=30)   # Plazo de pago en días
    contact_person = Column(String(100))    # Persona de contacto
    bank_iban = Column(String(255))         # IBAN cifrado con encrypt_secret_value
    default_discount = Column(Float, default=0.0)  # Descuento % por defecto
    notes_internal = Column(Text)           # Notas internas (no aparecen en PDF)

    # Status
    is_active = Column(Boolean, default=True)

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    company = relationship("Company", back_populates="clients")
    documents = relationship("Document", back_populates="client")

    # Unique constraint: code unique per company
    __table_args__ = (
        UniqueConstraint('company_id', 'code', name='uq_client_company_code'),
    )

    def __repr__(self):
        return f"<Client {self.code}: {self.name}>"
