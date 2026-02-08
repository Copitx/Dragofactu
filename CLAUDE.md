# CLAUDE.md

Archivo de contexto esencial para agentes AI trabajando en Dragofactu.

> **Para historial completo, sesiones anteriores y guías detalladas:** ver `MEMORIA_LARGO_PLAZO.md`

---

## CONTEXTO BASE

**Qué es:** ERP de escritorio para gestión empresarial: facturación, inventario, clientes, proveedores, trabajadores y diario.

**Stack Tecnológico:**
- Python 3.10+ / PySide6 (Qt6) - GUI
- SQLAlchemy 2.0 - ORM
- SQLite (dev) / PostgreSQL (prod)
- bcrypt + JWT - Autenticación
- ReportLab - PDFs
- FastAPI - Backend API

**Estructura Principal:**
```
dragofactu/
├── main.py              # Entry point modular
├── models/entities.py   # User, Client, Product, Document, Worker, DiaryEntry
├── services/api_client.py     # Cliente HTTP con cache offline
├── services/offline_cache.py  # Cache local + cola operaciones + monitor conectividad
├── ui/styles.py         # Sistema de diseño global
└── config/translation.py   # es/en/de

backend/
├── app/main.py          # FastAPI entry point
├── app/api/v1/*.py      # Endpoints REST
├── app/models/*.py      # SQLAlchemy models
└── app/schemas/*.py     # Pydantic schemas
```

**Archivos Raíz Clave:**
- `dragofactu_complete.py` - Versión monolítica (~7000 líneas)
- `start_dragofactu.sh` → lanza app
- `pyproject.toml` - Dependencias
- `.env` - Configuración local

---

## ESTADO ACTUAL DEL PROYECTO

**Versión:** v2.4.1 (2026-02-08)
**URL Producción:** https://dragofactu-production.up.railway.app

| Componente | Estado |
|------------|--------|
| Backend API | ✅ EN PRODUCCIÓN (Railway) |
| Desktop Client | ✅ FUNCIONAL (modo híbrido) |
| Tests Backend | ✅ 131 PASSING |
| PostgreSQL | ✅ CONFIGURADO (Railway) |
| PDF en remoto | ✅ COMPLETADO |

### Fases Completadas
| Fase | Descripción | Estado |
|------|-------------|--------|
| 1-6 | Backend API + Modelos + Auth + CRUD | ✅ |
| 7 | Testing (103 tests) | ✅ |
| 8 | Deployment Railway | ✅ |
| 9 | Integración Desktop (modo híbrido) | ✅ |
| 10 | Tabs con API remota | ✅ |
| 11 | PostgreSQL en Railway | ✅ |
| 12 | Onboarding/Registro empresa | ✅ |
| 13 | Sincronización/Cache offline | ✅ |
| 14 | Testing completo (103 tests) | ✅ |
| 15 | Seguridad + CI/CD | ✅ |
| 16 | Features backend (export, audit, reports) | ✅ |
| 17 | UI/UX (dark mode, shortcuts, toasts, tables) | ✅ |

### Todas las Tabs Soportan Modo Híbrido
Dashboard, Clientes, Productos, Documentos, Inventario, Diario, Trabajadores

---

## COMANDOS ESENCIALES

```bash
# Desktop
source venv/bin/activate
python3 dragofactu_complete.py

# Backend local
cd backend && source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Tests
cd backend && python -m pytest tests/ -v
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
- **Deducción stock:** Al marcar factura como PAID
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
```

---

## ARCHIVOS CLAVE

| Archivo | Propósito |
|---------|-----------|
| `dragofactu_complete.py` | App monolítica desktop |
| `dragofactu/services/api_client.py` | Cliente HTTP singleton |
| `backend/app/main.py` | Entry point FastAPI |
| `backend/app/api/v1/*.py` | Endpoints REST |
| `~/.dragofactu/tokens.json` | JWT tokens persistidos |
| `~/.dragofactu/app_mode.json` | Configuración modo local/remoto |
| `~/.dragofactu/pdf_settings.json` | Configuración PDF empresa |
| `~/.dragofactu/cache/*.json` | Cache offline de datos API |
| `~/.dragofactu/pending_operations.json` | Cola de operaciones pendientes |

---

## NOTAS PARA AGENTES

1. **Leer antes de modificar** - No asumas el contenido de archivos
2. **Verificar app_mode** - Antes de CUALQUIER `SessionLocal()`
3. **Usar UIStyles** - Para consistencia visual
4. **No hardcodear credenciales** - Usar env vars
5. **Commits pequeños** - Un commit por feature/fix
6. **Testing rápido:** `python3 dragofactu_complete.py`
7. **Backend en producción** - No tocar a menos que sea necesario

### Variables de Entorno (.env)
```bash
DATABASE_URL=sqlite:///dragofactu.db
DEBUG=true
SECRET_KEY=tu-clave-secreta-32-chars
DEFAULT_LANGUAGE=es
```

---

## PENDIENTES PRIORITARIOS

- [x] PDF generation en modo remoto
- [x] Fase 13: Sincronización/cache offline
- [x] **Fase 14:** Testing completo (103 tests backend, TODOs resueltos)
- [x] **Fase 15:** Seguridad (CORS configurable, validación inputs, request logging) + CI/CD (GitHub Actions)
- [x] **Fase 16:** Features backend (export/import CSV, audit log, informes)
- [x] **Fase 17:** Mejoras UI/UX (tema oscuro, atajos, notificaciones toast, tablas mejoradas)
- [ ] **Fase 18:** Producción y monitoreo (health check avanzado, backups, métricas)

> **Plan detallado paso a paso de cada fase:** ver `MEMORIA_LARGO_PLAZO.md` § "Fases Futuras"

---

## REFERENCIA HISTÓRICA

Para información detallada sobre:
- Sesiones de desarrollo anteriores
- Sistema de diseño UI completo
- Modelos de datos detallados
- Arquitectura de servicios
- Guías paso a paso para fases futuras
- Plan de migración original

**Ver:** `MEMORIA_LARGO_PLAZO.md`
