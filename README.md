# Dragofactu - Business Management System

A modern, desktop-based Enterprise Resource Planning (ERP) application built with Python and PySide6. Dragofactu provides comprehensive business management tools including invoicing, inventory control, client management, and document generation.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PySide6](https://img.shields.io/badge/GUI-PySide6-green.svg)](https://wiki.qt.io/Qt_for_Python)

## Screenshots

<p align="center">
  <img src="Screenshots/panelprincipal.png" alt="Main Dashboard" width="600"/>
  <br><em>Main Dashboard with business metrics and quick actions</em>
</p>

<p align="center">
  <img src="Screenshots/login.png" alt="Login Screen" width="600"/>
  <br><em>Secure login interface</em>
</p>

<p align="center">
  <img src="Screenshots/clientesmenu.png" alt="Client Management" width="600"/>
  <br><em>Client management with complete CRUD operations</em>
</p>

<p align="center">
  <img src="Screenshots/documentosprincipal.png" alt="Document Management" width="600"/>
  <br><em>Document management - Invoices, quotes, and delivery notes</em>
</p>

## Features

### Core Business Management
- **Dashboard** - Real-time business metrics, recent activity, and quick actions
- **Client Management** - Complete CRUD operations with search and filtering
- **Product/Inventory Management** - Stock control with low-stock alerts
- **Document Management** - Create and manage quotes, invoices, and delivery notes
- **Worker Management** - Employee records and role-based access control

### Document System
- **Quotes (Presupuestos)** - PRE-* automatic numbering
- **Invoices (Facturas)** - FAC-* automatic numbering with tax calculations
- **Delivery Notes (Albaranes)** - ALB-* automatic numbering
- **Document States** - Draft, Sent, Accepted, Paid, Partially Paid
- **PDF Generation** - Professional PDF output with company branding

### Additional Features
- **Multi-language Support** - Spanish, English, German
- **Personal Diary** - Notes and task management with date-based organization
- **Import/Export** - CSV and JSON data import/export capabilities
- **Modern UI** - Clean, professional interface with consistent design system
- **Role-based Access Control** - User permissions and authentication

## Technology Stack

- **Frontend:** PySide6 (Qt for Python)
- **Backend:** Python 3.8+
- **Database:** SQLAlchemy ORM (SQLite default, PostgreSQL support)
- **PDF Generation:** ReportLab
- **Authentication:** bcrypt, PyJWT
- **Configuration:** python-dotenv

## Installation

### Requirements
- Python 3.8 or higher
- pip (Python package manager)
- Git

### Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/Dragofactu.git
cd Dragofactu

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database with default admin user
python3 scripts/init_db.py

# Launch application
./start_dragofactu.sh
```

### Alternative Launch Methods

```bash
# Direct execution (for development)
python3 dragofactu_complete.py

# Using the modular package entry point
python3 -m dragofactu.main
```

## Configuration

Create a `.env` file in the root directory (or copy from `.env.example`):

```env
# Database Configuration
DATABASE_URL=sqlite:///dragofactu.db
# For PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost:5432/dragofactu

# Application Settings
APP_NAME=Dragofactu
DEBUG=false
DEFAULT_LANGUAGE=es  # es, en, or de

# Security
SECRET_KEY=your-secret-key-here
JWT_EXPIRE_HOURS=24

# UI Settings
WINDOW_WIDTH=1200
WINDOW_HEIGHT=800
```

### Default Credentials

**Important:** Change these credentials after first login.

- **Username:** `admin`
- **Password:** `admin123`

## Project Structure

```
Dragofactu/
├── dragofactu/              # Main application package
│   ├── models/              # SQLAlchemy ORM models
│   │   ├── entities.py      # Business entities (User, Client, Product, etc.)
│   │   ├── database.py      # Database configuration
│   │   └── base.py          # SQLAlchemy Base
│   ├── services/            # Business logic layer
│   │   ├── auth/            # Authentication service
│   │   ├── business/        # CRUD services with permissions
│   │   ├── documents/       # Document management
│   │   ├── inventory/       # Stock management
│   │   ├── pdf/             # PDF generation
│   │   └── diary/           # Personal notes/diary
│   ├── ui/                  # PySide6 UI components
│   │   ├── views/           # Individual view modules
│   │   └── styles.py        # Centralized design system
│   ├── config/              # Configuration and translations
│   │   ├── config.py        # Environment configuration
│   │   ├── translation.py   # Multi-language support
│   │   └── translations/    # Language files (es/en/de)
│   └── main.py             # Modular entry point
├── scripts/                 # Utility scripts
│   └── init_db.py          # Database initialization
├── Screenshots/             # Application screenshots
├── dragofactu_complete.py  # Monolithic entry point (development)
├── launch_dragofactu_fixed.py  # GUI launcher
├── start_dragofactu.sh     # Primary launch script
├── requirements.txt         # Python dependencies
├── .env.example            # Environment configuration template
├── CLAUDE.md               # AI assistant development guide
└── README.md               # This file
```

## Database

### SQLite (Default)
The application uses SQLite by default, creating `dragofactu.db` in the root directory. This is suitable for single-user installations and development.

### PostgreSQL (Production)
For multi-user environments, configure PostgreSQL in your `.env` file:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/dragofactu
```

### Database Initialization

```bash
# Create tables and default admin user
python3 scripts/init_db.py

# The script will create:
# - All necessary database tables
# - Default admin user (admin/admin123)
# - Required initial data
```

## Development

### Architecture

The application follows a layered architecture:

1. **Models Layer** - SQLAlchemy ORM entities with relationships
2. **Services Layer** - Business logic with `@require_permission` decorators
3. **UI Layer** - PySide6 views with centralized styling
4. **Configuration Layer** - Environment-based settings and translations

### Key Patterns

- **Permission-based Authorization** - Services use decorators for access control
- **Session Management** - Context managers for database sessions
- **Soft Deletes** - `is_active` flag instead of hard deletes
- **Document Workflow** - State machine for document status transitions
- **Automatic Codes** - Sequential document numbering (PRE-*, FAC-*, ALB-*)

### Testing

```bash
# Run with virtual environment activated
python3 dragofactu_complete.py
```

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add docstrings to functions and classes
- Update tests for new features
- Maintain the existing architecture patterns
- Do not commit `.env` files or database files

## Security Considerations

- Change default admin credentials immediately
- Use strong SECRET_KEY in production
- Keep `.env` file secure and never commit it
- Use PostgreSQL for multi-user deployments
- Regular database backups recommended
- Keep dependencies updated

## Troubleshooting

### Database Issues
```bash
# Reset database (WARNING: destroys all data)
rm dragofactu.db
python3 scripts/init_db.py
```

### Permission Errors
- Ensure the application has write permissions in its directory
- Check that the database file is not locked by another process

### GUI Issues
- Verify PySide6 is properly installed: `pip install --upgrade PySide6`
- On Linux, ensure Qt dependencies are installed

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [PySide6](https://wiki.qt.io/Qt_for_Python) - Qt for Python
- Database powered by [SQLAlchemy](https://www.sqlalchemy.org/)
- PDF generation by [ReportLab](https://www.reportlab.com/)

## Support

For bug reports and feature requests, please open an issue on GitHub.

---

**Version:** 1.0.0
**Status:** Production Ready
**Developed with Python by Dragofactu Team**
