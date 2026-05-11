"""
CompanyExpense model — libro de gastos / dietario financiero.
Replica exactamente el workflow del Dietario Excel:
  Fecha | Proveedor | Concepto | Nº Factura | Neto | IVA | Total | Estado | Observaciones
"""
import enum
import uuid

from sqlalchemy import Column, String, Float, Date, Text, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base, GUID


class ExpenseStatus(str, enum.Enum):
    PENDING = "pending"    # Pendiente
    PAID = "paid"          # Pagado
    PARTIAL = "partial"    # A cuenta (pago parcial)


class ExpenseCat(str, enum.Enum):
    MATERIAL = "material"
    LABOR = "labor"            # Mano de obra
    PAYROLL = "payroll"        # Nómina
    FUEL = "fuel"              # Combustible/gasoil
    UTILITIES = "utilities"    # Suministros (luz, agua)
    SUBCONTRACT = "subcontract"
    TAX = "tax"                # Impuestos / tasas / licencias
    OTHER = "other"


class CompanyExpense(Base):
    """
    Gasto de empresa — entrada del libro de gastos (dietario).
    Multi-tenant: toda query filtrada por company_id.
    """
    __tablename__ = "company_expenses"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    company_id = Column(GUID(), ForeignKey("companies.id"), nullable=False, index=True)

    # ── Campos principales (equivalentes al Excel) ──────────────────────────
    expense_date = Column(Date, nullable=False, index=True)
    supplier = Column(String(200), nullable=False, index=True)   # Proveedor
    concept = Column(String(300), nullable=False)                # Concepto
    invoice_ref = Column(String(100))                            # Nº Factura proveedor

    # ── Importes ────────────────────────────────────────────────────────────
    net_amount = Column(Float)          # Neto (puede ser nulo si solo se sabe el total)
    vat_rate = Column(Float)            # % IVA aplicado (21, 10, 0...)
    vat_amount = Column(Float)          # Importe IVA calculado
    total_amount = Column(Float, nullable=False)  # Total — campo siempre obligatorio

    # ── Clasificación ───────────────────────────────────────────────────────
    category = Column(String(50))       # ExpenseCat value

    # ── Estado de pago ──────────────────────────────────────────────────────
    status = Column(String(20), nullable=False, default="pending")
    payment_method = Column(String(50))  # Transferencia, Efectivo, Cheque...
    payment_date = Column(Date)          # Fecha real de pago
    paid_by = Column(String(50))         # Iniciales / nombre de quien pagó

    # ── Vinculación opcional a obra ─────────────────────────────────────────
    project_id = Column(GUID(), ForeignKey("projects.id"), nullable=True, index=True)

    # ── Notas libres (Observaciones en el Excel) ────────────────────────────
    notes = Column(Text)

    # ── Auditoría ───────────────────────────────────────────────────────────
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # ── Relationships ────────────────────────────────────────────────────────
    company = relationship("Company")
    project = relationship("Project")
    user = relationship("User")

    def __repr__(self):
        return f"<CompanyExpense {self.expense_date} {self.supplier} {self.total_amount}€>"
