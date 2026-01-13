# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Dragofactu is a desktop business management application (ERP) built with Python/PySide6 for the GUI and SQLAlchemy for database operations. It handles invoicing, inventory, client management, and business documents.

## Development Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Run the application (primary method)
./start_dragofactu.sh

# Run directly (alternative for development)
python3 dragofactu_complete.py

# Initialize/reset database with admin user
python3 scripts/init_db.py
```

## Architecture

### Entry Points
- `start_dragofactu.sh` → `launch_dragofactu_fixed.py` → launches GUI
- `dragofactu_complete.py` - Standalone monolithic application with all UI/business logic (~3000 lines)
- `dragofactu/main.py` - Modular entry point using the package structure

### Core Package Structure (`dragofactu/`)
- **models/** - SQLAlchemy ORM models
  - `entities.py` - All domain entities (User, Client, Product, Document, DocumentLine, Worker, etc.)
  - `database.py` - Engine/session configuration, supports SQLite and PostgreSQL
  - `base.py` - SQLAlchemy Base class
- **services/** - Business logic layer
  - `auth/auth_service.py` - Authentication and password hashing
  - `business/entity_services.py` - CRUD services with permission decorators (ClientService, SupplierService, ProductService)
  - `documents/document_service.py` - Document (invoice/quote/delivery note) management
  - `inventory/inventory_service.py` - Stock management
  - `diary/diary_service.py` - Personal notes/diary
- **ui/views/** - PySide6 UI components
  - `main_window.py` - Tab-based main window with menu/toolbar
  - `*_view.py` - Individual tab views (dashboard, clients, documents, inventory, diary)
- **config/** - Application configuration
  - `config.py` - Environment-based configuration (AppConfig class)
  - `translation.py` - Multi-language support (es/en/de)

### Key Patterns
- Services use `@require_permission('resource.action')` decorator for authorization
- Database sessions obtained via `SessionLocal()` context manager
- Soft deletes via `is_active` flag on most entities
- Document types: QUOTE, DELIVERY_NOTE, INVOICE with status workflow (DRAFT → SENT → ACCEPTED → PAID)
- Automatic document codes: PRE-*, FAC-*, ALB-*

### Database
- Default: SQLite at `dragofactu.db`
- Configuration via `DATABASE_URL` env var or `.env` file
- UUID primary keys on all entities
- Relationships use SQLAlchemy `relationship()` with proper back_populates

### Default Credentials
- Username: `admin`
- Password: Set via `DEFAULT_ADMIN_PASSWORD` env var or defaults to `change-this-password-2024`

## Configuration

Key environment variables (see `.env` or `.env.example`):
- `DATABASE_URL` - Database connection string
- `DEBUG` - Enable debug logging
- `DEFAULT_LANGUAGE` - UI language (es/en/de)
- `PDF_COMPANY_*` - Company info for PDF generation

## UI Visual System (Approved)
- Style: Apple-inspired, clean, minimal
- Backgrounds: #FAFAFA (app), white cards
- Text: #1D1D1F primary, #6E6E73 secondary
- Accent: #007AFF
- Font: system-ui / SF Pro / Segoe UI fallback
- Border radius: 8px standard, 12px cards
- Spacing: 4px grid, 16px card gaps
- Buttons: Primary blue, Secondary outline, Danger red
- Tables: clean, hover states, uppercase headers
