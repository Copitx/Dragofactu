# CLAUDE.md

Archivo de contexto esencial para agentes AI trabajando en Dragofactu.

> **Para historial completo, sesiones anteriores y guías detalladas:** ver `MEMORIA_LARGO_PLAZO.md`

---

## CONTEXTO BASE

**Qué es:** ERP empresarial con 3 clientes: desktop (PySide6), web (React), y API REST (FastAPI).

**Stack Tecnológico:**
- **Desktop:** Python 3.10+ / PySide6 (Qt6) / SQLAlchemy 2.0 / ReportLab
- **Backend:** FastAPI / PostgreSQL (prod) / SQLite (dev) / bcrypt + JWT
- **Frontend Web:** React 18 + TypeScript + Vite 5 + TailwindCSS + shadcn/ui

**Estructura Principal:**
```
dragofactu/                    # Desktop client (PySide6)
├── main.py                    # Entry point modular
├── models/entities.py         # ORM models
├── services/api_client.py     # Cliente HTTP con cache offline
├── services/offline_cache.py  # Cache local + cola operaciones
├── ui/styles.py               # Sistema de diseño global
└── config/translation.py      # es/en/de

backend/                       # API REST (FastAPI) - EN PRODUCCIÓN
├── app/main.py                # FastAPI entry point
├── app/api/v1/*.py            # Endpoints REST
├── app/models/*.py            # SQLAlchemy models
└── app/schemas/*.py           # Pydantic schemas

frontend/                      # Web client (React) - EN DESARROLLO
├── package.json               # Dependencias npm
├── vite.config.ts             # Proxy API en dev
├── tailwind.config.ts         # Paleta Dragofactu
└── src/
    ├── api/                   # Axios clients por entidad
    ├── components/            # shadcn/ui + layout + common
    ├── hooks/                 # TanStack Query hooks
    ├── stores/                # Zustand (auth, ui)
    ├── pages/                 # Lazy-loaded pages
    ├── i18n/                  # es.json, en.json, de.json
    └── types/                 # TypeScript interfaces
```

**Archivos Raíz Clave:**
- `dragofactu_complete.py` - App desktop monolítica (~7000 líneas)
- `start_dragofactu.sh` → lanza app desktop
- `pyproject.toml` - Dependencias Python
- `.env` - Configuración local

---

## ESTADO ACTUAL DEL PROYECTO

**Versión:** v2.5.0 (backend) / v3.0.0-dev (frontend web)
**URL Producción Backend:** https://dragofactu-production.up.railway.app

| Componente | Estado |
|------------|--------|
| Backend API | ✅ EN PRODUCCIÓN (Railway) |
| Desktop Client | ✅ FUNCIONAL (modo híbrido) |
| **Frontend Web** | **✅ COMPLETADO (PWA, todas las fases)** |
| Tests Backend | ✅ 144 PASSING |
| PostgreSQL | ✅ CONFIGURADO (Railway) |
| Monitoring | ✅ Health checks, métricas, Sentry |

### Fases Backend + Desktop (1-18) - COMPLETADAS
| Fase | Descripción | Estado |
|------|-------------|--------|
| 1-6 | Backend API + Modelos + Auth + CRUD | ✅ |
| 7 | Testing (103 tests) | ✅ |
| 8 | Deployment Railway | ✅ |
| 9-10 | Integración Desktop + Tabs híbridas | ✅ |
| 11-12 | PostgreSQL + Onboarding | ✅ |
| 13 | Sincronización/Cache offline | ✅ |
| 14-15 | Testing completo + Seguridad + CI/CD | ✅ |
| 16 | Features backend (export, audit, reports) | ✅ |
| 17 | UI/UX desktop (dark mode, shortcuts, toasts) | ✅ |
| 18 | Producción y monitoreo | ✅ |

### Fases Frontend Web (19-25) - EN DESARROLLO
| Fase | Descripción | Estado |
|------|-------------|--------|
| 19 | Scaffolding + Auth + Routing | ✅ |
| 20 | Layout + Dashboard | ✅ |
| **21** | **CRUD Clientes/Productos/Proveedores** | **✅** |
| 22 | Documentos (line editor, status, PDF) | ✅ |
| 23 | Inventario, Workers, Diary, Reminders | ✅ |
| 24 | Reports, Export/Import, Audit, Admin, Settings | ✅ |
| **25** | **PWA + Mobile + Deploy + Testing** | **✅** |

> **Plan detallado de fases 19-25:** ver `PLAN_FRONTEND.md`

---

## COMANDOS ESENCIALES

```bash
# Desktop
source venv/bin/activate
python3 dragofactu_complete.py

# Backend local
cd backend && source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Tests backend
cd backend && python -m pytest tests/ -v

# Frontend web (desarrollo)
cd frontend && npm install && npm run dev    # http://localhost:5173
cd frontend && npm run build                 # Build producción
cd frontend && npx tsc --noEmit              # Type check
```

**Credenciales Default:** `admin` / `admin123`

---

## PATRONES IMPORTANTES

### Patrón Modo Híbrido (Local/Remoto)
```python
def refresh_data(self):
    app_mode = get_app_mode()
    try:
        if app_mode.is_remote:
            self._refresh_from_api(app_mode.api)
        else:
            self._refresh_from_local()
    except Exception as e:
        logger.error(f"Error: {e}")

def _refresh_from_api(self, api):
    response = api.list_clients(limit=500)
    items = response.get("items", [])
    # Fill table from dicts

def _refresh_from_local(self):
    with SessionLocal() as db:
        items = db.query(Model).filter(Model.is_active == True).all()
        # Fill table from ORM objects
```

### Conversión UUID (Obligatoria)
```python
doc_id = self.document_id
if isinstance(doc_id, str):
    doc_id = uuid.UUID(doc_id)
```

### Traducción de Estados
```python
status_text = get_status_label(doc.status)  # "Pagado", "Borrador"
status_value = get_status_value("Pagado")    # "paid"
```

### Cache Offline (Fase 13)
```python
# El APIClient cachea automáticamente GET responses
# y devuelve datos cacheados si el servidor no responde.
# Detectar datos en cache:
response = api.list_clients(limit=500)
if response.get("_from_cache"):
    # Mostrar indicador al usuario

# Cola de operaciones pendientes:
from dragofactu.services.offline_cache import get_operation_queue
queue = get_operation_queue()
queue.add("create", "clients", {"code": "C001", "name": "Test"})
queue.sync(api_client)  # Cuando haya conexión
```

### Sistema de Traducción
```python
from dragofactu.config.translation import translator
translator.t("clients.title")  # Soporta claves anidadas
```

---

## LÓGICA DE NEGOCIO

- **Códigos automáticos:** `PRE-2026-00001`, `FAC-2026-00001`, `ALB-2026-00001`
- **Tipos documento:** QUOTE, DELIVERY_NOTE, INVOICE
- **Estados:** DRAFT → NOT_SENT → SENT → ACCEPTED → PAID
- **Deducción stock:** Al crear factura (permite stock negativo)
- **Soft delete:** `is_active=False`
- **Multi-tenancy:** Queries filtradas por `company_id`

---

## ENDPOINTS API PRINCIPALES

```
POST /api/v1/auth/login        # JWT tokens
POST /api/v1/auth/register     # Crear empresa + admin
GET  /api/v1/auth/me           # Usuario actual

GET/POST /api/v1/clients       # CRUD clientes
GET/POST /api/v1/products      # CRUD productos
GET/POST /api/v1/documents     # CRUD documentos

POST /api/v1/documents/{id}/change-status
POST /api/v1/products/{id}/adjust-stock
GET  /api/v1/dashboard/stats

GET  /api/v1/export/clients      # Export CSV
GET  /api/v1/export/products     # Export CSV
GET  /api/v1/export/suppliers    # Export CSV
POST /api/v1/export/import/clients   # Import CSV
POST /api/v1/export/import/products  # Import CSV
GET  /api/v1/audit               # Audit log
GET  /api/v1/reports/monthly     # Informe mensual
GET  /api/v1/reports/quarterly   # Informe trimestral
GET  /api/v1/reports/annual      # Informe anual

GET  /api/v1/admin/system-info   # Info sistema (admin only)
GET  /api/v1/admin/backup-info   # Info backups (admin only)

GET  /health                     # Liveness probe
GET  /health/ready               # Readiness probe (verifica DB)
GET  /metrics                    # Métricas de requests
```

---

## ARCHIVOS CLAVE

| Archivo | Propósito |
|---------|-----------|
| `dragofactu_complete.py` | App monolítica desktop |
| `dragofactu/services/api_client.py` | Cliente HTTP singleton (desktop) |
| `backend/app/main.py` | Entry point FastAPI |
| `backend/app/api/v1/*.py` | Endpoints REST |
| `frontend/src/api/client.ts` | Axios client + refresh interceptor (web) |
| `frontend/src/stores/auth-store.ts` | Auth state (Zustand persist) |
| `frontend/src/App.tsx` | Router + providers (web) |
| `Dockerfile` | Multi-stage build (Node + Python) |
| `PLAN_FRONTEND.md` | Plan completo fases 19-25 frontend |
| `~/.dragofactu/tokens.json` | JWT tokens desktop |
| `~/.dragofactu/app_mode.json` | Configuración modo local/remoto |

---

## NOTAS PARA AGENTES

1. **Leer antes de modificar** - No asumas el contenido de archivos
2. **Una fase a la vez** - No mezclar fases. Completar, verificar y commitear cada una por separado
3. **Verificar app_mode** (desktop) - Antes de CUALQUIER `SessionLocal()`
4. **Backend en producción** - No tocar a menos que sea estrictamente necesario
5. **Frontend: respetar patrones existentes** - shadcn/ui, TanStack Query, Zustand, i18n
6. **Commits pequeños** - Un commit por feature/fix
7. **Actualizar documentación** - Al terminar cada fase, actualizar CLAUDE.md, MEMORIA_LARGO_PLAZO.md y PLAN_FRONTEND.md

### Variables de Entorno (.env)
```bash
DATABASE_URL=sqlite:///dragofactu.db
DEBUG=true
SECRET_KEY=tu-clave-secreta-32-chars
DEFAULT_LANGUAGE=es
SENTRY_DSN=               # Opcional: DSN de Sentry para error tracking
```

---

## PENDIENTES PRIORITARIOS

- [x] Fases 1-18: Backend + Desktop completos
- [x] Fase 19: Frontend scaffolding + auth + routing
- [x] Fase 20: Layout (sidebar, header, mobile nav) + Dashboard con API real
- [x] Fase 21: CRUD Clientes/Productos/Proveedores (DataTable reutilizable)
- [x] Fase 22: Documentos (line editor, status transitions, PDF)
- [x] Fase 23: Inventario, Workers, Diary, Reminders
- [x] Fase 24: Reports, Export/Import, Audit, Admin, Settings
- [x] Fase 25: PWA + Mobile + Deploy + Testing

> **Plan detallado frontend:** ver `PLAN_FRONTEND.md`
> **Historial y referencia:** ver `MEMORIA_LARGO_PLAZO.md`
