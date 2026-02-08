# DRAGOFACTU - Sistema de Gestion Empresarial

**Version:** v2.5.0 (Backend) / v3.0.0-dev (Frontend Web)
**Estado:** Backend en produccion | Frontend web en desarrollo activo
**URL Produccion:** https://dragofactu-production.up.railway.app

---

## Arquitectura

Dragofactu es un ERP multi-plataforma con tres clientes:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Desktop App    │────▶│                 │────▶│  PostgreSQL     │
│  (PySide6)      │ JWT │  FastAPI API    │     │  (Railway)      │
└─────────────────┘     │  (Backend)      │     └─────────────────┘
                        │                 │
┌─────────────────┐     │  Multi-tenant   │
│  Frontend Web   │────▶│  (company_id)   │
│  (React + TS)   │ JWT │                 │
└─────────────────┘     └─────────────────┘
```

| Modo | Stack | Estado |
|------|-------|--------|
| **Backend API** | FastAPI + PostgreSQL | En produccion (Railway) |
| **Desktop** | PySide6 (Qt6) + modo hibrido | Funcional |
| **Frontend Web** | React 18 + TypeScript + Vite 5 | En desarrollo |

---

## Que es Dragofactu

ERP completo para gestion empresarial:

- **Facturacion**: Presupuestos, facturas, albaranes con workflow de estados
- **Inventario**: Stock con alertas y deduccion automatica al facturar
- **Clientes/Proveedores**: CRUD completo con busqueda y paginacion
- **Trabajadores**: Gestion de personal y cursos de formacion
- **Diario y Recordatorios**: Notas con prioridad y fechas limite
- **Informes**: Reportes mensuales, trimestrales y anuales
- **Export/Import**: CSV para clientes, productos, proveedores
- **Audit Log**: Registro de todas las acciones del sistema
- **Multi-idioma**: ES/EN/DE con cambio en vivo
- **Dark Mode**: Tema oscuro/claro/sistema
- **Cache Offline**: Desktop funciona sin conexion

---

## Instalacion Rapida

### Frontend Web (Desarrollo)

```bash
cd frontend
npm install
npm run dev
# Disponible en http://localhost:5173
```

### Backend API (Local)

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# API en http://localhost:8000 | Docs en http://localhost:8000/docs
```

### Desktop (Standalone)

```bash
./start_dragofactu.sh
```

**Credenciales por defecto:** `admin` / `admin123`

---

## Estructura del Proyecto

```
Dragofactu/
├── backend/                    # FastAPI Backend (Produccion)
│   ├── app/
│   │   ├── api/v1/            # Endpoints REST (50+)
│   │   ├── models/            # SQLAlchemy ORM (11 modelos)
│   │   ├── schemas/           # Pydantic v2 schemas
│   │   ├── core/              # Seguridad, config, DB
│   │   └── main.py            # FastAPI app
│   └── tests/                 # 144 tests pytest
│
├── frontend/                   # React Web Client
│   ├── src/
│   │   ├── api/               # Axios clients por entidad
│   │   ├── components/        # shadcn/ui + layout + data-table
│   │   ├── hooks/             # TanStack Query hooks
│   │   ├── stores/            # Zustand (auth, ui)
│   │   ├── pages/             # Lazy-loaded pages (CRUD)
│   │   ├── i18n/              # es.json, en.json, de.json
│   │   ├── types/             # TypeScript interfaces
│   │   └── lib/               # Utils, validators (Zod)
│   ├── vite.config.ts         # Proxy API → Railway
│   └── tailwind.config.ts     # Paleta Dragofactu
│
├── dragofactu/                 # Desktop Client (PySide6)
│   ├── services/api_client.py # Cliente HTTP con cache offline
│   ├── models/                # ORM models
│   ├── ui/                    # Componentes Qt
│   └── config/                # Traduccion, settings
│
├── dragofactu_complete.py      # App monolitica desktop
└── start_dragofactu.sh         # Entry point desktop
```

---

## API Endpoints

### Autenticacion
| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Registrar empresa + admin |
| POST | `/api/v1/auth/login` | Login → JWT tokens |
| POST | `/api/v1/auth/refresh` | Renovar access token |
| GET | `/api/v1/auth/me` | Info usuario actual |

### CRUD (Requieren JWT)
| Recurso | Endpoints | Extra |
|---------|-----------|-------|
| `/clients` | GET, POST, GET/:id, PUT/:id, DELETE/:id | Busqueda, paginacion |
| `/products` | GET, POST, GET/:id, PUT/:id, DELETE/:id | Stock, categorias |
| `/products/:id/adjust-stock` | POST | Ajustar stock +/- |
| `/suppliers` | GET, POST, GET/:id, PUT/:id, DELETE/:id | Busqueda, paginacion |
| `/documents` | GET, POST, GET/:id, PUT/:id, DELETE/:id | Workflow estados |
| `/documents/:id/change-status` | POST | Transiciones validadas |
| `/workers` | GET, POST, GET/:id, PUT/:id, DELETE/:id | Cursos |
| `/diary` | GET, POST, GET/:id, PUT/:id, DELETE/:id | Pin toggle |
| `/reminders` | GET, POST, GET/:id, PUT/:id, DELETE/:id | Prioridad, completar |
| `/dashboard/stats` | GET | Metricas dashboard |

### Export/Import & Reports
| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| GET | `/api/v1/export/clients` | Export CSV clientes |
| GET | `/api/v1/export/products` | Export CSV productos |
| GET | `/api/v1/export/suppliers` | Export CSV proveedores |
| POST | `/api/v1/export/import/clients` | Import CSV clientes |
| POST | `/api/v1/export/import/products` | Import CSV productos |
| GET | `/api/v1/audit` | Log de auditoria |
| GET | `/api/v1/reports/monthly` | Informe mensual |
| GET | `/api/v1/reports/quarterly` | Informe trimestral |
| GET | `/api/v1/reports/annual` | Informe anual |

### Admin & Monitoring
| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| GET | `/health` | Liveness probe |
| GET | `/health/ready` | Readiness probe (verifica DB) |
| GET | `/metrics` | Metricas de requests |
| GET | `/api/v1/admin/system-info` | Info sistema (admin) |
| GET | `/api/v1/admin/backup-info` | Info backups (admin) |

---

## Testing

```bash
cd backend
source venv/bin/activate
python -m pytest tests/ -v

# Resultado: 144 tests passing
# test_auth.py:          13 tests
# test_clients.py:       12 tests
# test_products.py:      12 tests
# test_documents.py:     12 tests
# test_suppliers.py:     12 tests
# test_workers.py:       13 tests
# test_diary.py:         10 tests
# test_reminders.py:     12 tests
# test_dashboard.py:      4 tests
# test_export_import.py: 12 tests
# test_audit.py:          7 tests
# test_reports.py:        8 tests
# test_health.py:         5 tests
# test_admin.py:          6 tests
# test_security.py:       6 tests
```

---

## Document Workflow

```
DRAFT → NOT_SENT → SENT → ACCEPTED → PAID
                 ↘        ↘ REJECTED
                  CANCELLED
```

Codigos automaticos: `PRE-2026-00001`, `FAC-2026-00001`, `ALB-2026-00001`

---

## Stack Tecnologico

| Componente | Tecnologia |
|------------|------------|
| Backend API | FastAPI + Uvicorn |
| Desktop GUI | PySide6 (Qt6) |
| Frontend Web | React 18 + TypeScript + Vite 5 |
| UI Components | shadcn/ui + TailwindCSS |
| State Management | Zustand + TanStack Query |
| Forms | react-hook-form + Zod |
| ORM | SQLAlchemy 2.0 |
| DB | PostgreSQL (prod) / SQLite (dev) |
| Auth | bcrypt + JWT |
| Validation | Pydantic v2 |
| PDF | ReportLab |
| Testing | pytest + httpx (144 tests) |
| CI/CD | GitHub Actions |
| Hosting | Railway |
| i18n | react-i18next / JSON translations |

---

## Changelog

### v3.0.0-dev (2026-02-08) - Frontend Web

**Fase 19-20: Scaffolding + Auth + Layout + Dashboard**
- Proyecto React 18 + TypeScript + Vite 5
- Autenticacion (login/register) con JWT
- Routing protegido con lazy loading
- Layout responsive (sidebar, header, mobile nav)
- Dashboard con 6 metricas desde API real
- i18n completo (ES/EN/DE) para toda la app
- Dark mode (claro/oscuro/sistema)
- shadcn/ui como sistema de componentes

**Fase 21: CRUD Clientes/Productos/Proveedores**
- DataTable reutilizable con busqueda y paginacion
- CRUD completo para clientes, productos, proveedores
- Formularios con validacion Zod
- Ajuste de stock desde la tabla de productos
- Dialogo de confirmacion para eliminacion
- TanStack Query hooks con cache e invalidacion
- Responsive: columnas se ocultan en mobile

### v2.5.0 (2026-02-07) - Produccion y Monitoreo
- Health checks (liveness + readiness)
- Metricas de requests
- Integracion Sentry
- Deploy en Railway con PostgreSQL

### v2.4.0 (2026-02-07) - Desktop UI/UX
- Dark mode completo
- Atajos de teclado (Ctrl+N, Ctrl+F, Ctrl+R...)
- Sistema de toasts/notificaciones
- Tablas ordenables por columna

### v2.3.0 (2026-02-07) - Features Backend
- Export/Import CSV para clientes, productos, proveedores
- Audit log con registro de acciones
- Reportes financieros (mensual, trimestral, anual)
- Panel de administracion

### v2.2.0 (2026-02-07) - Testing Completo
- 144 tests pytest passing
- Cobertura de todas las entidades y endpoints
- CI/CD con GitHub Actions

### v2.1.0 (2026-02-07) - Cache Offline
- Cache local de respuestas API
- Cola de operaciones pendientes
- Sincronizacion al recuperar conexion

### v2.0.0 (2026-02-02) - Multi-tenant API
- Backend FastAPI con 50+ endpoints
- 11 modelos SQLAlchemy con multi-tenancy
- JWT con access/refresh tokens
- RBAC: admin, management, warehouse, read_only
- Workflow de documentos con transiciones validadas
- Deduccion automatica de stock

---

## Despliegue

Backend desplegado en **Railway** (produccion):

```bash
# Variables de entorno
DATABASE_URL=postgresql://...
SECRET_KEY=<32-char-random>
DEBUG=false
ALLOWED_ORIGINS=http://localhost:5173,https://tuapp.com
```

Frontend en desarrollo local con proxy a produccion via `vite.config.ts`.

---

## Licencia

MIT License

---

**Desarrollado por DRAGOFACTU Team con asistencia de Claude (Anthropic)**
