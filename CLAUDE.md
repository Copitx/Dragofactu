# CLAUDE.md

Archivo de contexto para agentes AI trabajando en Dragofactu.

---

## CONTEXTO BASE DRAGOFACTU

**Qué es:** ERP de escritorio para gestión empresarial: facturación, inventario, clientes, proveedores, trabajadores y diario.

**Stack Tecnológico:**
- Python 3.10+ / PySide6 (Qt6) - GUI
- SQLAlchemy 2.0 - ORM
- SQLite (dev) / PostgreSQL (prod)
- bcrypt + JWT - Autenticación
- ReportLab - PDFs

**Estructura Principal:**
```
dragofactu/
├── main.py              # Entry point modular
├── models/
│   ├── entities.py      # User, Client, Product, Document, Worker, DiaryEntry
│   ├── database.py      # Engine + SessionLocal
│   └── audit.py         # DocumentHistory, StockMovement, Payment
├── services/
│   ├── auth/auth_service.py       # Login, JWT, permisos
│   ├── business/entity_services.py # CRUD clientes/productos/proveedores
│   ├── documents/document_service.py
│   ├── inventory/inventory_service.py
│   ├── diary/diary_service.py
│   └── pdf/pdf_service.py
├── ui/
│   ├── styles.py        # Sistema de diseño global
│   └── views/           # login_dialog, main_window, *_view.py
└── config/
    ├── config.py        # AppConfig (env vars)
    └── translation.py   # es/en/de
```

**Archivos Raíz Clave:**
- `start_dragofactu.sh` → lanza `launch_dragofactu_fixed.py`
- `dragofactu_complete.py` - Versión monolítica (~6200 líneas)
- `pyproject.toml` - Dependencias y entry point
- `.env` - Configuración (DATABASE_URL, DEBUG, SECRET_KEY)
- `dragofactu.db` - BD SQLite

**Flujo de Ejecución:**
```
start_dragofactu.sh
  → launch_dragofactu_fixed.py (setup venv, DB, display)
    → dragofactu.main:main()
      → DragofactuApp() → LoginDialog → MainWindow
```

**Comandos:**
```bash
source venv/bin/activate
./start_dragofactu.sh          # Producción
python3 dragofactu_complete.py  # Dev rápido
python3 scripts/init_db.py      # Reset BD + crear admin
```

**Credenciales Default:** `admin` / `admin123`

**Patrones Clave:**
- Decorador `@require_permission('resource.action')` en servicios
- Soft delete con `is_active=False`
- UUIDs como PKs
- Tipos documento: QUOTE, DELIVERY_NOTE, INVOICE
- Estados: DRAFT, NOT_SENT, SENT, ACCEPTED, REJECTED, PAID, PARTIALLY_PAID, CANCELLED
- Flujo típico: DRAFT → NOT_SENT → SENT → ACCEPTED → PAID
- Códigos automáticos: PRE-*, FAC-*, ALB-*

**Dependencias Críticas (pyproject.toml):**
```
PySide6>=6.5.0, sqlalchemy>=2.0.0, bcrypt>=3.2.0
reportlab>=4.0.0, python-dotenv>=1.0.0, alembic>=1.12.0
```

---

## HISTORIAL DE VERSIONES

| Versión | Fecha | Descripción |
|---------|-------|-------------|
| v1.0.0 | Inicial | Versión base con estructura modular |
| v1.0.0.1 | - | Primera iteración funcional |
| v1.0.0.2 | - | Fix crítico DetachedInstanceError (SQLAlchemy session) |
| v1.0.0.3 | - | Unificación de entry points (start_dragofactu.sh funcional) |
| v1.0.0.4 | - | CRUD completo, fixes críticos, seguridad mejorada |
| v1.0.0.5 | - | Cambios interfaz visual |
| v1.0.0.6 | - | Sesión Claude - Rediseño UI Apple-inspired |
| v1.0.0.7 | 2026-01-31 | Sesión Claude - Sistema de Traducción Completo |
| v1.0.0.9 | 2026-02-01 | Sesión Claude - Mejoras DocumentDialog, Estados, Recordatorios |
| v2.0.0 | 2026-02-02 | Backend API Multi-tenant + 52 tests |

---

## MIGRACIÓN MULTI-TENANT API (v2.0.0)

**Rama Git:** `feature/multi-tenant-api` (pushed to GitHub, listo para merge a main)
**Documento de Planificación:** `pasos a seguir migracion.md`
**Estado:** Fase 7 COMPLETADA - Backend testeado, listo para deployment
**Última actualización:** 2026-02-02 18:45

### Objetivo
Convertir Dragofactu de app desktop local a sistema multi-empresa con backend API centralizado.

### Arquitectura
```
Desktop Client (PySide6)  ──HTTP/REST──▶  FastAPI Backend  ──▶  PostgreSQL
     └── APIClient                              └── Multi-tenancy (company_id)
```

### Fases de Implementación

| Fase | Descripción | Estado | Commit |
|------|-------------|--------|--------|
| 1 | Setup Inicial (estructura, Docker, Company) | ✅ | `fb477b6` |
| 2 | Backend Core (modelos, schemas) | ✅ | `bcca59d` |
| 3 | Sistema de Autenticación (JWT) | ✅ | `7c2d31e` |
| 4 | CRUD Endpoints (35+ endpoints) | ✅ | `9658b57` |
| 5 | Documentos e Inventario | ✅ | `956ddde` |
| 6 | Cliente Desktop (APIClient) | ✅ | `6b9d920` |
| 7 | Testing (52 tests pytest) | ✅ | `aacae4e` |
| 8 | Despliegue (Railway free) | 🔄 | En curso |

### Estructura Backend Completa
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app con lifespan
│   ├── config.py            # Pydantic Settings
│   ├── database.py          # SQLAlchemy engine (SQLite dev)
│   ├── models/              # 9 archivos, 11 tablas
│   │   ├── base.py          # Base + GUID type portable
│   │   ├── company.py       # Tenant principal
│   │   ├── user.py          # User + UserRole + RBAC
│   │   ├── client.py        # company_id
│   │   ├── supplier.py      # company_id
│   │   ├── product.py       # company_id + stock
│   │   ├── document.py      # Document + DocumentLine + Status
│   │   ├── worker.py        # Worker + Course
│   │   ├── diary.py         # DiaryEntry
│   │   └── reminder.py      # Reminder
│   ├── schemas/             # 11 archivos Pydantic
│   │   ├── base.py, auth.py, company.py, client.py
│   │   ├── supplier.py, product.py, document.py
│   │   ├── worker.py, diary.py, reminder.py
│   ├── api/
│   │   ├── deps.py          # get_db, get_current_user, require_permission
│   │   ├── router.py        # Router principal
│   │   └── v1/
│   │       ├── auth.py      # login, register, refresh, me, logout
│   │       ├── clients.py   # CRUD
│   │       ├── products.py  # CRUD + adjust-stock
│   │       ├── suppliers.py # CRUD
│   │       ├── workers.py   # CRUD + courses
│   │       ├── diary.py     # CRUD
│   │       ├── reminders.py # CRUD + complete
│   │       └── documents.py # CRUD + change-status + convert + stats
│   └── core/
│       └── security.py      # hash_password, verify_password, JWT tokens
├── alembic/
├── venv/
├── dragofactu_api.db        # SQLite desarrollo
├── Dockerfile
├── docker-compose.yml       # PostgreSQL + API + Adminer
├── requirements.txt
└── .env.example
```

### APIClient Desktop
**Archivo:** `dragofactu/services/api_client.py`
```python
from dragofactu.services.api_client import get_api_client

client = get_api_client("http://localhost:8000")
client.login("admin", "password")
clientes = client.list_clients()
factura = client.create_document("invoice", client_id, issue_date, lines)
client.change_document_status(doc_id, "paid")  # Descuenta stock
```

### Endpoints API (45+ totales)
```
# Auth
POST /api/v1/auth/register     # Crear empresa + admin
POST /api/v1/auth/login        # JWT tokens
POST /api/v1/auth/refresh      # Renovar token
GET  /api/v1/auth/me           # Usuario actual
POST /api/v1/auth/logout

# CRUD (patrón repetido para cada entidad)
GET    /api/v1/clients         # Listar con filtros
POST   /api/v1/clients         # Crear
GET    /api/v1/clients/{id}    # Obtener
PUT    /api/v1/clients/{id}    # Actualizar
DELETE /api/v1/clients/{id}    # Soft delete

# Products (extra)
POST /api/v1/products/{id}/adjust-stock

# Documents (extra)
POST /api/v1/documents/{id}/change-status  # Valida transiciones, descuenta stock
POST /api/v1/documents/{id}/convert        # Presupuesto -> Factura
GET  /api/v1/documents/stats/summary       # Dashboard

# Reminders (extra)
POST /api/v1/reminders/{id}/complete
```

### Lógica de Negocio Implementada
- **Códigos automáticos:** `PRE-2026-00001`, `FAC-2026-00001`, `ALB-2026-00001`
- **Cálculos:** subtotal, IVA 21%, total
- **Transiciones de estado validadas:** DRAFT→NOT_SENT→SENT→ACCEPTED→PAID
- **Deducción stock:** Al marcar factura como PAID
- **Multi-tenancy:** Todas las queries filtradas por company_id
- **Permisos RBAC:** admin, management, warehouse, read_only

### Comandos Backend
```bash
# Desarrollo (SQLite)
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Con Docker (PostgreSQL) - PENDIENTE configurar
docker-compose up -d
```

### URLs
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Testing (Fase 7 - Completada)
```bash
cd backend
source venv/bin/activate
python -m pytest tests/ -v

# 52 tests passing:
# - test_auth.py: 13 tests (login, register, refresh, logout, password security)
# - test_clients.py: 12 tests (CRUD + multi-tenancy isolation)
# - test_products.py: 11 tests (CRUD + stock adjustment)
# - test_documents.py: 12 tests (workflow + stock deduction + conversion)
# - test_health.py: 4 tests (health check + OpenAPI)
```

**Archivos de test:**
- `backend/tests/conftest.py` - Fixtures (db, client, test_user, auth_headers)
- `backend/pytest.ini` - Configuración pytest

**Fixes durante testing:**
- Dual Base class issue: `database.py` ahora importa Base de `models.base`
- StaticPool para SQLite in-memory en tests
- Correcto workflow de estados: DRAFT→NOT_SENT→SENT→ACCEPTED→PAID

### Deployment Railway (Fase 8)

**IMPORTANTE:** Railway debe usar `backend/` como directorio raíz, NO la raíz del repositorio.

**Configuración en Railway Dashboard:**
1. Service Settings → Root Directory: `backend`
2. O usar el Dockerfile que ya está configurado

**Archivos de configuración:**
```
backend/
├── railway.toml      # Configuración Railway (builder, start command)
├── Procfile          # Fallback para Heroku-style
├── nixpacks.toml     # Configuración Nixpacks
├── Dockerfile        # Docker build (usa PORT env var)
└── .railwayignore    # Archivos a excluir del deploy
```

**Variables de entorno REQUERIDAS en Railway:**
```bash
DATABASE_URL=postgresql://user:pass@host:5432/dbname  # Railway PostgreSQL
SECRET_KEY=<generar-32-chars-aleatorios>              # Para JWT
DEBUG=false                                            # Producción
ALLOWED_ORIGINS=http://localhost,https://tuapp.com    # CORS
```

**Generar SECRET_KEY seguro:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Comando de inicio:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**URLs después del deploy:**
- API: https://tu-app.railway.app
- Health: https://tu-app.railway.app/health
- Docs: https://tu-app.railway.app/docs

### Pendientes
- [x] Fase 8: Configuración Railway
- [ ] Verificar deploy funciona en Railway
- [ ] Configurar PostgreSQL en Railway
- [ ] Integrar APIClient en UI de dragofactu_complete.py

---

## SESIÓN 2026-02-02: Migración Multi-Tenant API (Claude Opus 4.5)
**AI Agent:** Claude Opus 4.5 (claude-opus-4-5-20251101)
**Fecha:** 2026-02-02
**Duración:** Sesión completa de implementación

### Resumen
Implementación completa del backend FastAPI multi-tenant para Dragofactu. Se creó toda la infraestructura desde cero en la rama `feature/multi-tenant-api`.

### Fases Completadas en Esta Sesión

**Fase 1: Setup Inicial**
- Estructura de carpetas backend/
- docker-compose.yml con PostgreSQL
- Modelo Company (tenant)
- Configuración Alembic

**Fase 2: Modelos y Schemas**
- 11 modelos SQLAlchemy con company_id
- Tipo GUID portable (SQLite/PostgreSQL)
- 11 schemas Pydantic con validación
- Enums: UserRole, DocumentType, DocumentStatus

**Fase 3: Autenticación JWT**
- core/security.py: bcrypt + JWT
- api/deps.py: get_current_user, require_permission
- Endpoints: login, register, refresh, me, logout
- Persistencia tokens en cliente

**Fase 4: CRUD Endpoints**
- 6 routers: clients, products, suppliers, workers, diary, reminders
- 35+ endpoints con filtros y paginación
- Soft delete, búsqueda, ordenación

**Fase 5: Documentos e Inventario**
- Router documents con lógica completa
- Códigos automáticos por tipo y año
- Transiciones de estado validadas
- Deducción automática de stock
- Conversión presupuesto→factura
- Endpoint stats para dashboard

**Fase 6: APIClient Desktop**
- Clase APIClient completa
- Métodos para todos los endpoints
- Manejo de tokens y refresh
- Singleton para acceso global

### Commits de Esta Sesión
```
fb477b6 - feat: Fase 1 - Setup inicial backend multi-tenant
bcca59d - feat: Fase 2 - Modelos y schemas completos con multi-tenancy
7c2d31e - feat: Fase 3 - Sistema de autenticacion JWT completo
9658b57 - feat: Fase 4 - CRUD endpoints completos
956ddde - feat: Fase 5 - Documents e inventario completo
6b9d920 - feat: Fase 6 - APIClient para cliente desktop
45dce7e - docs: Actualizar progreso Fase 6 completada
```

### Archivos Creados (principales)
```
backend/app/main.py
backend/app/config.py
backend/app/database.py
backend/app/models/*.py (9 archivos)
backend/app/schemas/*.py (11 archivos)
backend/app/api/deps.py
backend/app/api/router.py
backend/app/api/v1/*.py (8 routers)
backend/app/core/security.py
dragofactu/services/api_client.py
docker-compose.yml
```

### Testing Verificado
- Register empresa + usuario admin
- Login con JWT tokens
- CRUD clientes, productos
- Crear factura con líneas
- Flujo: DRAFT→NOT_SENT→SENT→ACCEPTED→PAID
- Stock descontado correctamente (50-5=45)
- APIClient funciona contra backend

### Decisiones Técnicas
1. **SQLite para desarrollo** en lugar de Docker/PostgreSQL (simplicidad)
2. **GUID type portable** para UUIDs (funciona en SQLite y PostgreSQL)
3. **bcrypt directo** en lugar de passlib (compatibilidad)
4. **Códigos con año:** PRE-2026-00001 para reinicio anual
5. **Soft delete:** is_active=False para mantener historial

---

## TRABAJO PREVIO DE AGENTES AI

### Sesión 2026-01-13: Rediseño UI (Claude)
**Archivo:** `docs/session-2026-01-13-ui-redesign.md`

**Completado:**
- [x] Sistema de diseño centralizado (`dragofactu/ui/styles.py`)
- [x] Clase `UIStyles` en `dragofactu_complete.py` (líneas 39-262)
- [x] Dashboard con métricas, quick actions, documentos recientes
- [x] MainWindow con menús limpios, tabs estilizados, status bar
- [x] LoginDialog con layout card-based
- [x] Todas las tabs de gestión actualizadas (Clientes, Productos, Documentos, Inventario, Diario)
- [x] Menús sin emojis + shortcuts (Ctrl+Shift+P, Ctrl+Shift+F, etc.)

**Pendiente (Next Steps):**
- [ ] Actualizar ClientDialog, ProductDialog, DocumentDialog styling
- [ ] Actualizar SettingsDialog styling
- [ ] Actualizar DiaryEntryDialog styling
- [ ] Añadir loading states/spinners
- [ ] Toast notifications en lugar de QMessageBox
- [ ] Considerar iconos estilo SF Symbols

### Sesión 2026-01-31: Sistema de Traducción Completo (Claude - opencode)
**AI Agent:** Claude (opencode) - Agente especializado en desarrollo de software con capacidad de lectura/escritura de archivos

**Objetivo:** Implementar sistema de traducción completo para toda la UI sin requerir reinicio de aplicación

**Completado:**
- [x] **Sistema Core de Traducción**: Enhanced `TranslationManager` con persistencia de idioma y soporte de claves anidadas
- [x] **Traducción Dashboard**: Métricas, títulos, acciones rápidas, documentos recientes
- [x] **Traducción de Todas las Tabs**: 
  - [x] `ClientManagementTab` - Título, botones, búsqueda, headers tabla
  - [x] `ProductManagementTab` - Título, botones, búsqueda, headers tabla  
  - [x] `DocumentManagementTab` - Título, botones, filtros, headers tabla
  - [x] `InventoryManagementTab` - Título, botones, filtros, estadísticas, headers tabla
  - [x] `DiaryManagementTab` - Título, botones, selector fecha, estadísticas
- [x] **Métodos retranslate_ui()**: Cada clase tiene método para actualizar textos sin reiniciar
- [x] **Integración MainWindow**: Actualización automática de toda la UI al cambiar idioma
- [x] **Archivos de Traducción Completos**: 
  - [x] Español (es.json) - 50+ nuevas claves añadidas
  - [x] Inglés (en.json) - Traducciones completas para todos los elementos
  - [x] Alemán (de.json) - Traducciones completas para todos los elementos
- [x] **Testing**: Aplicación iniciada correctamente, login funcional, UI traducida

**Características Implementadas:**
- ✅ **Cambio de Idioma en Vivo**: Toda la UI actualiza instantáneamente
- ✅ **Persistencia de Preferencia**: Guarda selección de idioma automáticamente
- ✅ **Soporte de Claves Anidadas**: `translator.t("menu.file")` navega estructura JSON
- ✅ **Sin Reinicios Requeridos**: Cambio de idioma sin perder estado
- ✅ **Cobertura Total**: 100+ elementos UI traducibles en 5 tabs + Dashboard

**Detalles Técnicos:**
```python
# Pattern implementado en cada tab:
def retranslate_ui(self):
    """Update all translatable text"""
    # Update title
    if hasattr(self, 'title_label'):
        self.title_label.setText(translator.t("clients.title"))
    
    # Update buttons, headers, etc.
```

**Archivos Modificados:**
- `dragofactu/config/translation.py` - Enhanced con persistencia y nested keys
- `dragofactu_complete.py` - Añadidos métodos retranslate_ui() a todas las clases
- `dragofactu/config/translations/es.json` - 50+ nuevas claves
- `dragofactu/config/translations/en.json` - Traducciones completas
- `dragofactu/config/translations/de.json` - Traducciones completas

### Sesión 2026-02-01: Mejoras Documentos, Estados y Recordatorios (Claude)
**AI Agent:** Claude Opus 4.5 - Agente especializado en desarrollo de software

**Objetivo:** Mejorar gestión de documentos, añadir nuevos estados, sistema de recordatorios y fixes críticos

**Completado:**
- [x] **Nuevos Estados DocumentStatus**: Añadidos `NOT_SENT`, `PARTIALLY_PAID`, `CANCELLED`
- [x] **Sistema de Traducción de Estados**: `STATUS_LABELS_ES`, `get_status_label()`, `get_status_value()`
- [x] **Filtro por Estado**: ComboBox en DocumentManagementTab para filtrar por estado
- [x] **Filtro Ordenar Por**: Ordenar documentos por fecha, código, cliente, total (asc/desc)
- [x] **DocumentDialog Mejorado**:
  - Modo edición completo con carga de datos existentes
  - Selector de cantidad al añadir productos
  - Tabla editable con spinboxes para cantidad/descuento
  - Conversión UUID correcta para evitar errores SQL
- [x] **Código Clickeable**: Click en código de documento abre editor completo
- [x] **Deducción Automática de Stock**: Al marcar factura como PAID, descuenta stock
- [x] **Sistema de Recordatorios**:
  - Modelo `Reminder` en entities.py
  - Botón "Nuevo Recordatorio" en Diario
  - Botón "Ver Recordatorios" con lista completa
  - Marcar completado/eliminar recordatorios
  - Widget Recordatorios en Dashboard
- [x] **Dashboard Mejorado**:
  - Sección "Documentos Pendientes" (izquierda)
  - Sección "Recordatorios" (derecha)
  - Fecha/hora en tiempo real
- [x] **Sincronización Entre Paneles**: Dashboard, Documentos, Inventario sincronizados

**Fixes Críticos:**
- Fix `'str' object has no attribute 'hex'` - Conversión UUID en `load_document_data()` y `save_document()`
- Fix botones acciones invisibles - Simplificados a texto plano (PDF, X)
- Fix comparación `due_date` con datetime vs date

**Patrones Importantes para Agentes:**
```python
# Conversión UUID obligatoria cuando document_id viene como string
doc_id = self.document_id
if isinstance(doc_id, str):
    doc_id = uuid.UUID(doc_id)

# Traducción de estados
status_text = get_status_label(doc.status)  # Devuelve "Pagado", "Borrador", etc.
status_value = get_status_value("Pagado")    # Devuelve "paid"

# Estados pendientes para Dashboard
pending_statuses = [
    DocumentStatus.DRAFT,
    DocumentStatus.SENT,
    DocumentStatus.ACCEPTED,
    DocumentStatus.PARTIALLY_PAID,
    DocumentStatus.NOT_SENT
]
```

**Archivos Modificados:**
- `dragofactu/models/entities.py` - Nuevos estados en DocumentStatus, modelo Reminder
- `dragofactu_complete.py` - DocumentDialog, filtros, recordatorios, sincronización

### Sesión 2026-02-01: Configuración PDF Personalizable (Claude Opus 4.5)
**AI Agent:** Claude Opus 4.5 (claude-opus-4-5-20251101) - Agente especializado en desarrollo de software
**Fecha:** 2026-02-01

**Objetivo:** Añadir herramienta en Ajustes para personalizar el contenido del PDF generado automáticamente (datos empresa, logo, texto pie de página)

**Completado:**
- [x] **Sistema de Configuración PDF Persistente**:
  - Nueva clase `PDFSettingsManager` con patrón Singleton
  - Archivo de configuración JSON en `~/.dragofactu/pdf_settings.json`
  - Métodos `save_settings()`, `get_settings()`, `reset_to_defaults()`
  - Gestión de logo: `copy_logo()`, `remove_logo()`
- [x] **Datos de Empresa Personalizables**:
  - Nombre de la empresa
  - Dirección completa
  - Teléfono
  - Email
  - CIF/NIF
- [x] **Logo de Empresa**:
  - Selector de archivo para PNG/JPG
  - Vista previa del logo seleccionado
  - Logo copiado a directorio de configuración
  - Dimensiones automáticas (máx. 40x20mm en PDF)
- [x] **Texto de Pie de Factura Personalizable**:
  - Campo QTextEdit multilinea
  - Soporte para saltos de línea
  - Permite avisos legales, condiciones de pago, etc.
- [x] **SettingsDialog Rediseñado**:
  - Estructura con QTabWidget (3 pestañas)
  - Tab "Configuración PDF" como primera pestaña
  - Tab "Apariencia" con ajustes UI
  - Tab "Sistema" con info BD y aplicación
  - Estilo consistente con UIStyles existente
- [x] **InvoicePDFGenerator Actualizado**:
  - Lee configuración desde PDFSettingsManager en lugar de AppConfig
  - Soporte para insertar logo en cabecera del PDF
  - Footer dinámico desde configuración
- [x] **Traducciones Añadidas**:
  - Nueva sección `settings` en es.json, en.json, de.json
  - 30+ nuevas claves de traducción

**Detalles Técnicos:**
```python
# Uso del PDFSettingsManager
from dragofactu_complete import get_pdf_settings

settings_mgr = get_pdf_settings()
settings = settings_mgr.get_settings()

# Guardar configuración
settings_mgr.save_settings({
    'company_name': 'Mi Empresa',
    'company_address': 'Calle Principal 123',
    'company_phone': '+34 912 345 678',
    'company_email': 'info@miempresa.com',
    'company_cif': 'B12345678',
    'logo_path': '/path/to/logo.png',
    'footer_text': 'Texto personalizado...'
})

# Copiar logo a directorio de configuración
new_path = settings_mgr.copy_logo('/path/to/source/logo.png')
```

**Archivos Modificados:**
- `dragofactu_complete.py` - Añadido `PDFSettingsManager`, `get_pdf_settings()`, modificado `InvoicePDFGenerator`, `SettingsDialog`
- `dragofactu/config/translations/es.json` - Nueva sección `settings`
- `dragofactu/config/translations/en.json` - Nueva sección `settings`
- `dragofactu/config/translations/de.json` - Nueva sección `settings`

**Ubicación de Archivos de Configuración:**
- Config: `~/.dragofactu/pdf_settings.json`
- Logo: `~/.dragofactu/company_logo.png`

### Sesión 2026-02-02: Backend API Multi-tenant + Testing (Claude Opus 4.5)
**AI Agent:** Claude Opus 4.5 (claude-opus-4-5-20251101)
**Fecha:** 2026-02-02

**Objetivo:** Completar la migración a arquitectura multi-tenant con backend FastAPI y suite de tests

**Fases Completadas en Esta Sesión:**
- [x] **Fase 7 - Testing**: Suite completa de 52 tests pytest
  - `test_auth.py`: 13 tests (login, register, refresh, logout, password security)
  - `test_clients.py`: 12 tests (CRUD + pagination + search + multi-tenancy)
  - `test_products.py`: 11 tests (CRUD + stock adjustment + low stock filter)
  - `test_documents.py`: 12 tests (create + workflow + stock deduction + conversion)
  - `test_health.py`: 4 tests (health check + OpenAPI docs)

**Fixes Importantes Durante Testing:**
- **Dual Base class bug**: `app.database.py` creaba su propio `Base` en lugar de importar de `app.models.base`. Corregido para usar única fuente de verdad.
- **SQLite in-memory StaticPool**: Añadido `StaticPool` para compartir conexión en tests
- **Workflow de estados**: Tests corregidos para seguir flujo correcto DRAFT→NOT_SENT→SENT→ACCEPTED→PAID

**Archivos Nuevos:**
```
backend/tests/
├── conftest.py      # Fixtures: db, client, test_user, auth_headers
├── test_auth.py     # 13 tests autenticación
├── test_clients.py  # 12 tests clientes
├── test_products.py # 11 tests productos
├── test_documents.py# 12 tests documentos
└── test_health.py   # 4 tests health
backend/pytest.ini   # Configuración pytest
```

**Archivos Modificados:**
- `backend/app/database.py` - Import Base de models.base, añadido StaticPool
- `backend/app/main.py` - Import Base corregido

**Comandos Testing:**
```bash
cd backend
source venv/bin/activate
python -m pytest tests/ -v          # Todos los tests
python -m pytest tests/test_auth.py # Solo auth tests
```

**Commits:**
- `aacae4e` - test: Add complete pytest test suite for backend API (52 tests)

**Estado Final:**
- Backend API 100% funcional con 52 tests passing
- Listo para merge a main
- Listo para deployment (Fase 8)

### V1.0.0.4: Estabilización Crítica (Claude)
**Archivo:** `STABILIZATION_COMPLETE.md`

**Fixes implementados:**
1. Import error `Product` en `inventory_service.py:266` - RESUELTO
2. Syntax error try/except en `start_fixed.py` - RESUELTO
3. Seguridad: credenciales env-based, JWT auto-generado - RESUELTO
4. Arquitectura: launcher unificado `launch_dragofactu.py` - RESUELTO

### V1.0.0.2: DetachedInstanceError Fix (Claude)
- Pre-extracción de datos de usuario en LoginDialog mientras sesión activa
- Uso de diccionario en lugar de objeto ORM desconectado

---

## TODOs PENDIENTES EN CÓDIGO

```
dragofactu/ui/views/dashboard_view.py:173    # TODO: Implement unpaid invoices
dragofactu/ui/views/dashboard_view.py:195    # TODO: Implement activity logging
dragofactu/ui/views/documents_view.py:19     # TODO: Implement documents table
dragofactu/ui/views/clients_view.py:19       # TODO: Implement clients table
```

---

## SISTEMA DE DISEÑO UI

### Paleta de Colores
| Token | Valor | Uso |
|-------|-------|-----|
| `bg_app` | `#FAFAFA` | Fondo app, paneles |
| `bg_card` | `#FFFFFF` | Cards, dialogs, inputs |
| `bg_hover` | `#F5F5F7` | Hover states |
| `text_primary` | `#1D1D1F` | Headings, texto principal |
| `text_secondary` | `#6E6E73` | Labels, descripciones |
| `text_tertiary` | `#86868B` | Hints, placeholders |
| `accent` | `#007AFF` | Botones primarios, links, selección |
| `accent_hover` | `#0056CC` | Button hover |
| `success` | `#34C759` | Estados positivos, pagado |
| `warning` | `#FF9500` | Alertas, stock bajo |
| `danger` | `#FF3B30` | Botones eliminar, errores |
| `border` | `#D2D2D7` | Bordes inputs |
| `border_light` | `#E5E5EA` | Bordes cards, divisores |

### Tipografía
- Font: `system-ui, -apple-system, "SF Pro Display", "Segoe UI", sans-serif`
- Sizes: 11px (xs), 12px (sm), 13px (base), 15px (lg), 17px (xl), 28px (títulos página)
- Headers: weight 600, uppercase para headers de tabla

### Espaciado
- Panel margins: 24-32px
- Card padding: 20px
- Card gaps: 16px
- Button padding: 10px 20px

### Border Radius
- Buttons/inputs: 8px
- Cards/dialogs: 12px

### Métodos UIStyles (dragofactu_complete.py)
```python
UIStyles.get_primary_button_style()   # Botón azul filled
UIStyles.get_secondary_button_style() # Botón outline
UIStyles.get_danger_button_style()    # Botón rojo filled
UIStyles.get_table_style()            # Tabla limpia con hover
UIStyles.get_input_style()            # Inputs, combos, date pickers
UIStyles.get_card_style()             # Contenedores card
UIStyles.get_panel_style()            # Fondos de tabs
UIStyles.get_group_box_style()        # Secciones agrupadas
UIStyles.get_label_style()            # Labels de formulario
UIStyles.get_status_label_style()     # Texto footer status
UIStyles.get_section_title_style()    # Headers de sección (17px)
```

### Principios de Diseño
1. **No emojis** en botones o menús
2. **Un solo color accent** (#007AFF) para elementos interactivos
3. **Bordes sutiles** (1px gris claro)
4. **Whitespace generoso** (24-32px margins)
5. **Headers tabla uppercase** con color secundario
6. **Ocultar grid lines** en tablas, usar bottom borders
7. **Hover states** en elementos interactivos
8. **Keyboard shortcuts** para acciones comunes

---

## CONFIGURACIÓN

### Variables de Entorno (.env)
```bash
DATABASE_URL=sqlite:///dragofactu.db  # o postgresql://...
DEBUG=true
LOG_LEVEL=INFO
SECRET_KEY=tu-clave-secreta-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24
DEFAULT_LANGUAGE=es                    # es/en/de
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=admin123        # CAMBIAR en producción
PDF_COMPANY_NAME=Mi Empresa
PDF_COMPANY_ADDRESS=Dirección
PDF_COMPANY_PHONE=+34 XXX XXX XXX
PDF_COMPANY_EMAIL=info@empresa.com
```

---

## MODELOS DE DATOS PRINCIPALES

### Entidades (dragofactu/models/entities.py)
- **User**: username, email, password_hash, role (ADMIN/MANAGEMENT/WAREHOUSE/READ_ONLY)
- **Client**: code, name, tax_id, address, city, phone, email
- **Supplier**: similar a Client
- **Product**: code, name, category, purchase_price, sale_price, current_stock, minimum_stock
- **Document**: code, type, status, issue_date, client_id, lines, tax_config
- **DocumentLine**: product_id, quantity, unit_price, discount_percent
- **Worker**: code, first_name, last_name, position, department, salary
- **Course**: worker_id, name, provider, issue_date, expiration_date
- **DiaryEntry**: title, content, entry_date, user_id, tags
- **Reminder**: title, description, due_date, priority (low/normal/high), is_completed, created_by

### Auditoría (dragofactu/models/audit.py)
- **DocumentHistory**: acción, cambios, snapshots
- **StockMovement**: movement_type (in/out/adjustment), stock_before/after
- **Payment**: document_id, amount, payment_method, status
- **SupplierInvoice**: code, supplier_id, invoice_number, total
- **EmailLog**: to_email, subject, status

---

## ARQUITECTURA DE SERVICIOS

Todos los servicios usan `@require_permission('resource.action')` para autorización.

### Permisos por Rol
- **ADMIN**: Acceso total
- **MANAGEMENT**: CRUD completo, sin usuarios
- **WAREHOUSE**: Inventario, productos (lectura docs)
- **READ_ONLY**: Solo lectura

### Servicios Disponibles
- `AuthService`: hash_password, verify_password, generate_token, authenticate
- `ClientService`: create, get, search, update, delete (soft)
- `SupplierService`: CRUD proveedores
- `ProductService`: CRUD productos con stock
- `DocumentService`: create, add_line, update_status, convert_to_invoice, export_pdf
- `InventoryService`: get_stock_levels, adjust_stock, get_low_stock_products
- `DiaryService`: CRUD entradas de diario
- `WorkerService`: CRUD trabajadores y cursos
- `PDFService`: generate_document_pdf (ReportLab)
- `EmailService`: envío SMTP

---

## DOCUMENTACIÓN ADICIONAL

- `docs/UI_DESIGN_SYSTEM.md` - Sistema de diseño completo con CSS/QSS
- `docs/session-2026-01-13-ui-redesign.md` - Log sesión rediseño UI
- `STABILIZATION_COMPLETE.md` - Resumen fixes v1.0.0.4
- `README_FINAL.md` - Estado funcional completo

---

## NOTAS PARA AGENTES

1. **Antes de modificar código**: Lee los archivos relevantes primero
2. **Versión monolítica vs modular**: `dragofactu_complete.py` tiene todo integrado, el paquete `dragofactu/` es modular
3. **Estilos UI**: Usar métodos de `UIStyles` para consistencia
4. **Base de datos**: Siempre usar `SessionLocal()` como context manager
5. **Seguridad**: No hardcodear credenciales, usar env vars
6. **Testing**: `python3 dragofactu_complete.py` para probar rápido
7. **Idiomas**: Usar `TranslationManager.t('key')` para textos traducibles

---

## PERFIL DEL AGENTE AI

**Identidad:** Claude (opencode) - Agente especializado en desarrollo de software
**Capacidades:** 
- Lectura y escritura de archivos completas
- Ejecución de comandos shell y bash
- Análisis y modificación de código complejo
- Búsqueda de patrones y refactoring
- Testing y validación de sistemas
- Gestión de proyectos git

**Modo Operativo:** Build (puede realizar cambios en archivos y sistema)

**Contexto de Sesión 2026-01-31:**
- Implementación completa de sistema de traducción UI
- Actualización de todas las tabs principales (Clients, Products, Documents, Inventory, Diary)
- Sistema de traducción en vivo sin reiniciar aplicación
- Archivos JSON actualizados para es/en/de
- Testing validado con aplicación funcional

**Stack Personal del Agente:**
- Python, PySide6, SQLAlchemy experto
- Patrones de traducción e internacionalización
- Diseño UI/UX consistente
- Gestión de archivos JSON y configuración
