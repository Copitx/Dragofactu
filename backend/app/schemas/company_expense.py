"""
Pydantic schemas for CompanyExpense (libro de gastos / dietario).
"""
from datetime import date, datetime
from typing import Optional, Dict, List
from pydantic import BaseModel, Field


class CompanyExpenseCreate(BaseModel):
    expense_date: date
    supplier: str = Field(..., max_length=200)
    concept: str = Field(..., max_length=300)
    invoice_ref: Optional[str] = Field(None, max_length=100)

    net_amount: Optional[float] = None
    vat_rate: Optional[float] = None      # e.g. 21.0, 10.0, 0.0
    vat_amount: Optional[float] = None
    total_amount: float

    category: Optional[str] = None        # ExpenseCat value
    status: Optional[str] = "pending"     # ExpenseStatus value
    payment_method: Optional[str] = None
    payment_date: Optional[date] = None
    paid_by: Optional[str] = None

    project_id: Optional[str] = None
    notes: Optional[str] = None


class CompanyExpenseUpdate(BaseModel):
    expense_date: Optional[date] = None
    supplier: Optional[str] = Field(None, max_length=200)
    concept: Optional[str] = Field(None, max_length=300)
    invoice_ref: Optional[str] = Field(None, max_length=100)

    net_amount: Optional[float] = None
    vat_rate: Optional[float] = None
    vat_amount: Optional[float] = None
    total_amount: Optional[float] = None

    category: Optional[str] = None
    status: Optional[str] = None
    payment_method: Optional[str] = None
    payment_date: Optional[date] = None
    paid_by: Optional[str] = None

    project_id: Optional[str] = None
    notes: Optional[str] = None


class MarkExpensePaidRequest(BaseModel):
    payment_method: Optional[str] = None
    payment_date: Optional[date] = None
    paid_by: Optional[str] = None


class CompanyExpenseResponse(BaseModel):
    id: str
    company_id: str
    expense_date: date
    supplier: str
    concept: str
    invoice_ref: Optional[str] = None

    net_amount: Optional[float] = None
    vat_rate: Optional[float] = None
    vat_amount: Optional[float] = None
    total_amount: float

    category: Optional[str] = None
    status: str
    payment_method: Optional[str] = None
    payment_date: Optional[date] = None
    paid_by: Optional[str] = None

    project_id: Optional[str] = None
    project_name: Optional[str] = None   # Joined from Project
    notes: Optional[str] = None

    user_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CompanyExpenseListResponse(BaseModel):
    items: List[CompanyExpenseResponse]
    total: int
    skip: int
    limit: int


class ExpenseMonthlySummary(BaseModel):
    year: int
    month: int
    total_amount: float
    pending_amount: float
    paid_amount: float
    partial_amount: float
    by_category: Dict[str, float]
    expense_count: int
    pending_count: int
    paid_count: int


class SupplierSuggestion(BaseModel):
    name: str
    last_used: Optional[date] = None
