"""
Financial report schemas.
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class DocumentTypeSummary(BaseModel):
    """Summary for a specific document type."""
    type: str
    count: int
    total: float


class PeriodReport(BaseModel):
    """Financial report for a time period."""
    period_start: datetime
    period_end: datetime
    total_invoiced: float
    total_quotes: float
    total_paid: float
    total_pending: float
    document_count: int
    by_type: List[DocumentTypeSummary]


class AnnualReport(BaseModel):
    """Annual report with monthly breakdown."""
    year: int
    total_invoiced: float
    total_paid: float
    total_pending: float
    months: List[PeriodReport]
