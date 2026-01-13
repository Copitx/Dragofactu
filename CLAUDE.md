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
- `dragofactu_complete.py` - Standalone monolithic application with all UI/business logic (~3500 lines)
- `dragofactu/main.py` - Modular entry point using the package structure

### Core Package Structure (`dragofactu/`)
- **models/** - SQLAlchemy ORM models
  - `entities.py` - All domain entities (User, Client, Product, Document, DocumentLine, Worker, etc.)
  - `database.py` - Engine/session configuration, supports SQLite and PostgreSQL
  - `base.py` - SQLAlchemy Base class
- **services/** - Business logic layer
  - `auth/auth_service.py` - Authentication and password hashing
  - `business/entity_services.py` - CRUD services with permission decorators
  - `documents/document_service.py` - Document management
  - `inventory/inventory_service.py` - Stock management
  - `diary/diary_service.py` - Personal notes/diary
- **ui/** - PySide6 UI components
  - `styles.py` - **Centralized design system stylesheet** (NEW)
  - `views/main_window.py` - Tab-based main window
  - `views/*_view.py` - Individual tab views
- **config/** - Application configuration
  - `config.py` - Environment-based configuration
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
- Password: `admin123` (or set via `DEFAULT_ADMIN_PASSWORD` env var)

## Configuration

Key environment variables (see `.env` or `.env.example`):
- `DATABASE_URL` - Database connection string
- `DEBUG` - Enable debug logging
- `DEFAULT_LANGUAGE` - UI language (es/en/de)
- `PDF_COMPANY_*` - Company info for PDF generation

---

## UI Design System (Implemented)

### Style Files
- `dragofactu/ui/styles.py` - Global stylesheet with `apply_stylesheet(app)` function
- `dragofactu_complete.py` - Contains `UIStyles` class with all design tokens

### Color Palette
| Token | Value | Usage |
|-------|-------|-------|
| `bg_app` | `#FAFAFA` | App background, panels |
| `bg_card` | `#FFFFFF` | Cards, dialogs, inputs |
| `bg_hover` | `#F5F5F7` | Hover states |
| `text_primary` | `#1D1D1F` | Headings, main text |
| `text_secondary` | `#6E6E73` | Labels, descriptions |
| `text_tertiary` | `#86868B` | Hints, placeholders |
| `accent` | `#007AFF` | Primary buttons, links, selection |
| `accent_hover` | `#0056CC` | Button hover |
| `success` | `#34C759` | Success states, paid status |
| `warning` | `#FF9500` | Warnings, low stock |
| `danger` | `#FF3B30` | Delete buttons, errors |
| `border` | `#D2D2D7` | Input borders |
| `border_light` | `#E5E5EA` | Card borders, dividers |

### Typography
- Font: `system-ui, -apple-system, "SF Pro Display", "Segoe UI", sans-serif`
- Sizes: 11px (xs), 12px (sm), 13px (base), 15px (lg), 17px (xl), 28px (page titles)
- Headers: 600 weight, uppercase for table headers

### Spacing
- Panel margins: 24-32px
- Card padding: 20px
- Card gaps: 16px
- Button padding: 10px 20px

### Border Radius
- Buttons/inputs: 8px
- Cards/dialogs: 12px

### Component Styles (UIStyles class methods)
```python
UIStyles.get_primary_button_style()   # Blue filled button
UIStyles.get_secondary_button_style() # Outline button
UIStyles.get_danger_button_style()    # Red filled button
UIStyles.get_table_style()            # Clean table with hover
UIStyles.get_input_style()            # Inputs, combos, date pickers
UIStyles.get_card_style()             # Card containers
UIStyles.get_panel_style()            # Tab backgrounds
UIStyles.get_group_box_style()        # Grouped sections
UIStyles.get_label_style()            # Form labels
UIStyles.get_status_label_style()     # Footer status text
UIStyles.get_section_title_style()    # Section headers (17px)
```

### UI Components Updated
- [x] Dashboard - Welcome section, metric cards, quick actions, recent documents
- [x] MainWindow - Clean menus with shortcuts, styled tabs, status bar
- [x] LoginDialog - Card-based form layout
- [x] ClientManagementTab - Header, toolbar, search, table
- [x] ProductManagementTab - Same pattern
- [x] DocumentManagementTab - Same pattern with filter
- [x] InventoryManagementTab - Stats cards with colored borders
- [x] DiaryManagementTab - Notes card, date picker, stats badges

### Design Principles
1. **No emojis** in buttons or menus (clean text only)
2. **Single accent color** (#007AFF) for all interactive elements
3. **Subtle borders** (1px light gray) instead of colored/bold borders
4. **Generous whitespace** (24-32px margins)
5. **Uppercase table headers** with secondary text color
6. **Hide grid lines** in tables, use bottom borders only
7. **Hover states** on interactive elements
8. **Keyboard shortcuts** for common actions
