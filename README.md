# Dragofactu - Professional Business Management System

A comprehensive desktop business management application designed for small to medium enterprises, built with Python and PySide6.

## Features

- **User Management**: Multi-user system with role-based permissions
- **Client Management**: Complete client database with contact information
- **Document Management**: Quotes, delivery notes, and invoices with full history tracking
- **Inventory Management**: Stock control with low-stock alerts
- **Supplier Management**: Supplier information and invoice tracking
- **Diary/Agenda**: Notion-like daily entries with attachments
- **Worker Management**: Employee records with course tracking
- **Payment Tracking**: Monitor payments and collections
- **PDF Generation**: Professional document exports
- **Email Integration**: Send documents directly from the application

## Architecture

The application follows clean architecture principles:

```
dragofactu/
├── models/          # Database models (SQLAlchemy)
├── services/        # Business logic layer
├── ui/              # User interface layer (PySide6)
├── config/          # Application configuration
├── utils/           # Utility functions
└── tests/           # Test suite
```

## Technology Stack

- **Language**: Python 3.11+
- **UI Framework**: PySide6 (Qt6)
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy 2.0+
- **PDF Generation**: ReportLab
- **Authentication**: JWT with bcrypt

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-org/dragofactu.git
cd dragofactu
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your database and email configuration
```

5. Run the application:
```bash
python -m dragofactu.main
```

## Configuration

The application uses environment variables for configuration. Copy `.env.example` to `.env` and configure:

- **Database**: PostgreSQL connection details
- **Email**: SMTP configuration for sending documents
- **Company**: Company information for PDF generation
- **Security**: Secret key for JWT tokens

## Database Setup

The application uses PostgreSQL. Create a database and update the configuration in `.env`:

```bash
# PostgreSQL setup
createdb dragofactu
```

The application will automatically create tables on first run.

## User Roles

The system includes predefined roles:

- **Admin**: Full system access
- **Management**: Client, supplier, and document management
- **Warehouse**: Inventory and product management
- **Read-only**: View-only access to all modules

## Document Types

Supports three main document types:

1. **Quotes**: Budget estimates for clients
2. **Delivery Notes**: Goods delivery tracking
3. **Invoices**: Billing documents with payment tracking

### Document Features

- Manual conversion between document types
- Complete audit history tracking
- Custom tax configuration per document/line
- Flexible line items (products or text)
- Payment status tracking

## Development

### Running Tests

```bash
pytest tests/
```

### Code Style

The project uses:
- **Black** for code formatting
- **Ruff** for linting
- **MyPy** for type checking

```bash
black dragofactu/
ruff check dragofactu/
mypy dragofactu/
```

### Database Migrations

When modifying models, create and apply migrations:

```bash
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Email: support@dragofactu.com

## Roadmap

- [ ] Advanced reporting dashboard
- [ ] Web application version
- [ ] Mobile app companion
- [ ] API integration
- [ ] Multi-currency support
- [ ] Advanced inventory features
- [ ] Project management module# Dragofactu
