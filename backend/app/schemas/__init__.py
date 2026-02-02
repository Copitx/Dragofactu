"""
Pydantic schemas package.
Request/Response schemas for the API.
"""
from app.schemas.base import BaseSchema, TimestampMixin, PaginatedResponse, MessageResponse

# Auth
from app.schemas.auth import (
    LoginRequest, LoginResponse, TokenResponse,
    RefreshRequest, RefreshResponse,
    RegisterCompanyRequest, UserResponse
)

# Company
from app.schemas.company import CompanyBase, CompanyUpdate, CompanyResponse

# Client
from app.schemas.client import (
    ClientBase, ClientCreate, ClientUpdate, ClientResponse, ClientList
)

# Supplier
from app.schemas.supplier import (
    SupplierBase, SupplierCreate, SupplierUpdate, SupplierResponse, SupplierList
)

# Product
from app.schemas.product import (
    ProductBase, ProductCreate, ProductUpdate, ProductResponse, ProductList,
    StockAdjustment
)

# Document
from app.schemas.document import (
    DocumentLineBase, DocumentLineCreate, DocumentLineResponse,
    DocumentBase, DocumentCreate, DocumentUpdate, DocumentResponse,
    DocumentSummary, DocumentList, StatusChange
)

# Worker
from app.schemas.worker import (
    CourseBase, CourseCreate, CourseResponse,
    WorkerBase, WorkerCreate, WorkerUpdate, WorkerResponse,
    WorkerSummary, WorkerList
)

# Diary
from app.schemas.diary import (
    DiaryEntryBase, DiaryEntryCreate, DiaryEntryUpdate,
    DiaryEntryResponse, DiaryEntryList
)

# Reminder
from app.schemas.reminder import (
    ReminderBase, ReminderCreate, ReminderUpdate,
    ReminderResponse, ReminderList
)

__all__ = [
    # Base
    'BaseSchema', 'TimestampMixin', 'PaginatedResponse', 'MessageResponse',
    # Auth
    'LoginRequest', 'LoginResponse', 'TokenResponse',
    'RefreshRequest', 'RefreshResponse',
    'RegisterCompanyRequest', 'UserResponse',
    # Company
    'CompanyBase', 'CompanyUpdate', 'CompanyResponse',
    # Client
    'ClientBase', 'ClientCreate', 'ClientUpdate', 'ClientResponse', 'ClientList',
    # Supplier
    'SupplierBase', 'SupplierCreate', 'SupplierUpdate', 'SupplierResponse', 'SupplierList',
    # Product
    'ProductBase', 'ProductCreate', 'ProductUpdate', 'ProductResponse', 'ProductList',
    'StockAdjustment',
    # Document
    'DocumentLineBase', 'DocumentLineCreate', 'DocumentLineResponse',
    'DocumentBase', 'DocumentCreate', 'DocumentUpdate', 'DocumentResponse',
    'DocumentSummary', 'DocumentList', 'StatusChange',
    # Worker
    'CourseBase', 'CourseCreate', 'CourseResponse',
    'WorkerBase', 'WorkerCreate', 'WorkerUpdate', 'WorkerResponse',
    'WorkerSummary', 'WorkerList',
    # Diary
    'DiaryEntryBase', 'DiaryEntryCreate', 'DiaryEntryUpdate',
    'DiaryEntryResponse', 'DiaryEntryList',
    # Reminder
    'ReminderBase', 'ReminderCreate', 'ReminderUpdate',
    'ReminderResponse', 'ReminderList',
]
