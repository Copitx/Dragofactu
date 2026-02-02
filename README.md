# DRAGOFACTU - Sistema de Gestion Empresarial

**Version:** 2.0.0 (Multi-tenant API)
**Estado:** Beta - Backend API + Desktop Client
**Stack:** Python 3.10+ / FastAPI / PySide6 / SQLAlchemy / SQLite|PostgreSQL

---

## Arquitectura

Dragofactu ahora soporta dos modos de operación:

| Modo | Descripción | Uso |
|------|-------------|-----|
| **Desktop Local** | App standalone con SQLite local | Uso personal, sin internet |
| **Multi-tenant API** | Backend FastAPI + Cliente Desktop | Multi-empresa, multi-usuario, cloud |

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Desktop App    │────▶│  FastAPI API    │────▶│  PostgreSQL     │
│  (PySide6)      │ JWT │  (Backend)      │     │  (Cloud DB)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │
                              ▼
                        Multi-tenancy
                        (company_id)
```

---

## Que es Dragofactu

ERP para gestion empresarial:
- **Facturacion**: Presupuestos, facturas, albaranes con workflow de estados
- **Inventario**: Stock con alertas y deduccion automatica al facturar
- **Clientes/Proveedores**: CRUD completo con busqueda
- **Trabajadores**: Gestion de personal y cursos de formacion
- **Diario**: Notas diarias con recordatorios
- **Multi-idioma**: ES/EN/DE con cambio en vivo

---

## Instalacion Rapida

### Modo Desktop Local (Standalone)

```bash
# Clonar repositorio
git clone https://github.com/Copitx/Dragofactu.git
cd Dragofactu

# Ejecutar (instalacion automatica)
./start_dragofactu.sh
```

**Credenciales por defecto:** `admin` / `admin123`

### Modo API Multi-tenant

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Iniciar servidor
uvicorn app.main:app --reload
# API disponible en http://localhost:8000
# Docs en http://localhost:8000/docs
```

---

## Estructura del Proyecto

```
Dragofactu/
├── backend/                    # 🆕 FastAPI Backend (API Multi-tenant)
│   ├── app/
│   │   ├── api/v1/            # Endpoints REST
│   │   │   ├── auth.py        # Login, register, JWT
│   │   │   ├── clients.py     # CRUD clientes
│   │   │   ├── products.py    # CRUD productos + stock
│   │   │   ├── documents.py   # Documentos + workflow
│   │   │   ├── suppliers.py   # CRUD proveedores
│   │   │   ├── workers.py     # CRUD trabajadores
│   │   │   ├── diary.py       # Entradas diario
│   │   │   └── reminders.py   # Recordatorios
│   │   ├── models/            # SQLAlchemy ORM (11 modelos)
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── core/security.py   # JWT + bcrypt
│   │   └── main.py            # FastAPI app
│   ├── tests/                 # 🆕 Pytest suite (52 tests)
│   └── requirements.txt
│
├── dragofactu/                # Paquete desktop modular
│   ├── services/
│   │   └── api_client.py      # 🆕 Cliente HTTP para API
│   ├── models/
│   ├── ui/
│   └── config/
│
├── dragofactu_complete.py     # App monolitica (modo local)
├── start_dragofactu.sh        # Entry point
└── docker-compose.yml         # 🆕 PostgreSQL para produccion
```

---

## API Endpoints

### Autenticación
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Registrar empresa + admin |
| POST | `/api/v1/auth/login` | Login → access_token + refresh_token |
| POST | `/api/v1/auth/refresh` | Renovar access_token |
| GET | `/api/v1/auth/me` | Info usuario actual |

### CRUD (Todos requieren JWT)
| Recurso | Endpoints | Descripción |
|---------|-----------|-------------|
| `/clients` | GET, POST, GET/:id, PUT/:id, DELETE/:id | Clientes |
| `/products` | GET, POST, GET/:id, PUT/:id, DELETE/:id | Productos |
| `/products/:id/adjust-stock` | POST | Ajustar stock |
| `/suppliers` | GET, POST, GET/:id, PUT/:id, DELETE/:id | Proveedores |
| `/documents` | GET, POST, GET/:id, PUT/:id, DELETE/:id | Documentos |
| `/documents/:id/change-status` | POST | Cambiar estado |
| `/documents/:id/convert` | POST | Convertir PRE→FAC/ALB |
| `/documents/stats/summary` | GET | Resumen dashboard |
| `/workers` | GET, POST, GET/:id, PUT/:id, DELETE/:id | Trabajadores |
| `/workers/:id/courses` | POST | Añadir curso |
| `/diary` | GET, POST, GET/:id, PUT/:id, DELETE/:id | Diario |
| `/reminders` | GET, POST, GET/:id, PUT/:id, DELETE/:id | Recordatorios |
| `/reminders/:id/complete` | POST | Marcar completado |

---

## Testing

```bash
cd backend
source venv/bin/activate
python -m pytest tests/ -v

# Resultado: 52 tests passing
# - test_auth.py: 13 tests
# - test_clients.py: 12 tests
# - test_products.py: 11 tests
# - test_documents.py: 12 tests
# - test_health.py: 4 tests
```

---

## Multi-tenancy

Cada empresa es un **tenant** aislado:

```python
# Modelo Company
class Company(Base):
    id = Column(GUID(), primary_key=True)
    code = Column(String(20), unique=True)  # Ej: "ACME001"
    name = Column(String(100))
    # ...

# Todos los modelos tienen company_id
class Client(Base):
    company_id = Column(GUID(), ForeignKey("companies.id"))
    # Unique constraint per company
    __table_args__ = (
        UniqueConstraint('company_id', 'code'),
    )
```

Los endpoints filtran automaticamente por `company_id` del usuario autenticado.

---

## Document Workflow

```
DRAFT → NOT_SENT → SENT → ACCEPTED → PAID
                 ↘        ↘ REJECTED
                  CANCELLED
```

- **DRAFT**: Editable, eliminable
- **NOT_SENT**: Listo para enviar
- **SENT**: Enviado al cliente
- **ACCEPTED**: Aceptado, puede convertirse
- **PAID**: Factura pagada (deduce stock automaticamente)
- **PARTIALLY_PAID**: Pago parcial
- **CANCELLED**: Cancelado

Codigos automaticos: `PRE-2026-00001`, `FAC-2026-00001`, `ALB-2026-00001`

---

## Changelog

### v2.0.0 (2026-02-02) - Multi-tenant API 🚀

**Backend FastAPI Completo:**
- Arquitectura multi-tenant con `company_id` en todas las entidades
- 11 modelos SQLAlchemy con relaciones
- 35+ endpoints REST documentados en OpenAPI
- Autenticación JWT con access/refresh tokens
- RBAC: admin, management, warehouse, read_only
- Workflow de documentos con transiciones validadas
- Deducción automática de stock al marcar PAID
- Conversión de presupuestos a facturas/albaranes

**Testing:**
- 52 tests pytest passing
- Cobertura: auth, clients, products, documents, health
- Fixtures con test database in-memory

**Cliente Desktop:**
- APIClient para comunicación con backend
- Token storage en `~/.dragofactu/api_tokens.json`
- Refresh token automático

**Archivos nuevos:**
- `backend/` - Estructura completa FastAPI
- `dragofactu/services/api_client.py` - Cliente HTTP
- `docker-compose.yml` - PostgreSQL para producción

### v1.0.0.9 (2026-02-01) - Documentos, Estados, Recordatorios

- Configuración PDF personalizable (logo, datos empresa)
- Nuevos estados: NOT_SENT, PARTIALLY_PAID, CANCELLED
- Sistema de recordatorios completo
- Dashboard mejorado con pendientes

### v1.0.0.8 (2026-01-31) - Sistema de Traducción

- Traducción UI completa ES/EN/DE
- Cambio de idioma en vivo sin reinicio

### v1.0.0.7 (2026-01-31) - Clean Repo

- Reducido de 457MB a 11MB
- Sistema de instalación mejorado

### v1.0.0.6 (2026-01-13) - UI Redesign

- Sistema de diseño Apple-inspired
- Clase UIStyles centralizada

---

## Stack Tecnologico

| Componente | Tecnología |
|------------|------------|
| Desktop GUI | PySide6 (Qt6) |
| Backend API | FastAPI + Uvicorn |
| ORM | SQLAlchemy 2.0 |
| DB Dev | SQLite |
| DB Prod | PostgreSQL |
| Auth | bcrypt + JWT (python-jose) |
| Validation | Pydantic v2 |
| PDF | ReportLab |
| Testing | pytest + httpx |
| i18n | JSON translations |

---

## Despliegue (Próximo)

El backend está preparado para desplegar en Railway (free tier):

```bash
# Variables de entorno necesarias
DATABASE_URL=postgresql://...
SECRET_KEY=<32-char-random>
DEBUG=false
ALLOWED_ORIGINS=http://localhost,https://tuapp.com
```

---

## Licencia

MIT License

---

**Desarrollado por DRAGOFACTU Team con asistencia de Claude (Anthropic)**
