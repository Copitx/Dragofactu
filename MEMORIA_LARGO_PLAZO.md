# MEMORIA_LARGO_PLAZO.md

> **Este archivo contiene el historial completo del proyecto Dragofactu.**
> Para el contexto operativo esencial, ver `CLAUDE.md`.
>
> Última actualización: 2026-02-06

---

## Tabla de Contenidos

1. [Historial de Versiones](#historial-de-versiones)
2. [Sesiones de Desarrollo por Fecha](#sesiones-de-desarrollo-por-fecha)
3. [Sistema de Diseño UI](#sistema-de-diseño-ui)
4. [Modelos de Datos](#modelos-de-datos)
5. [Arquitectura de Servicios](#arquitectura-de-servicios)
6. [Migración Multi-Tenant API - Detalles](#migración-multi-tenant-api---detalles)
7. [Fases Futuras - Guías Paso a Paso](#fases-futuras---guías-paso-a-paso)
8. [TODOs Pendientes en Código](#todos-pendientes-en-código)
9. [Plan de Migración Original](#plan-de-migración-original)

---

## Historial de Versiones

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
| v2.0.1 | 2026-02-06 | Fix auto-login + WorkersManagementTab + mejoras APIClient |
| v2.0.2 | 2026-02-06 | Fix errores 422/500: límites paginación y timezone reminders |

---

## Sesiones de Desarrollo por Fecha

### Sesión 2026-02-06: Fix Auto-login + WorkersManagementTab
**AI Agent:** Claude Opus 4.5 (claude-opus-4-5-20251101)

#### Resumen
Arreglo del sistema de auto-login con tokens guardados y creación de la nueva tab de Trabajadores.

#### Cambios Implementados

**1. Fix Sistema de Auto-login**
- **Problema:** La app siempre mostraba LoginDialog aunque había tokens válidos guardados
- **Solución:** Nuevo método `App.try_auto_login()` que valida tokens con `/auth/me` antes de mostrar login
- **Archivo:** `dragofactu_complete.py` (clase App)

**2. Singleton APIClient Unificado**
- **Problema:** `AppMode.api` creaba instancias separadas de APIClient
- **Solución:** `AppMode.api` ahora usa `get_api_client()` del módulo singleton
- **Archivos:** `dragofactu_complete.py`, `dragofactu/services/api_client.py`

**3. Mejora _refresh_token()**
- **Problema:** Borraba tokens en errores de red (no solo en rechazo del servidor)
- **Solución:** Solo borrar tokens si servidor devuelve 401/403 explícitamente
- **Archivo:** `dragofactu/services/api_client.py`

**4. Nueva WorkersManagementTab**
- **Descripción:** Tab completa de gestión de trabajadores con soporte híbrido local/remoto
- **Funcionalidades:**
  - Listado con filtro por departamento
  - Búsqueda por nombre, código o departamento
  - CRUD completo (crear, editar, eliminar)
  - Soporte modo local (SQLite) y remoto (API)
- **Archivo:** `dragofactu_complete.py` (clase WorkersManagementTab, WorkerDialog)

**5. Traducciones Workers**
- **Archivos:** `dragofactu/config/translations/es.json`, `en.json`, `de.json`
- **Sección nueva:** `workers` con 17 claves de traducción

#### Archivos Modificados
| Archivo | Cambios |
|---------|---------|
| `dragofactu_complete.py` | +600 líneas (App.try_auto_login, WorkersManagementTab, WorkerDialog) |
| `dragofactu/services/api_client.py` | reset_api_client(), mejora _refresh_token() |
| `dragofactu/config/translations/es.json` | Sección workers |
| `dragofactu/config/translations/en.json` | Sección workers |
| `dragofactu/config/translations/de.json` | Sección workers |

---

### Revisión 2026-02-06: Auditoría del Código
**AI Agent:** Claude Opus 4.5
**Evaluación:** 7/10

#### Problemas Encontrados y Corregidos
| # | Problema | Archivo | Estado |
|---|----------|---------|--------|
| 1 | Schema `ClientCreate` no aceptaba `is_active` → Error 400 | backend/schemas/client.py | ✅ |
| 2 | Schema `ClientUpdate` no aceptaba `is_active` | backend/schemas/client.py | ✅ |
| 3 | `_get_user_reminders()` no usa API en modo remoto | Dashboard línea ~1417 | ✅ |
| 4 | `edit_document()` ignora app_mode | DocumentManagementTab | ✅ |
| 5 | `view_document()` siempre recarga desde BD local | DocumentManagementTab | ✅ |
| 6 | Error 422 "limit>100" en list_clients/products/etc | backend/api/v1/*.py | ✅ |
| 7 | Error 500 al crear/listar reminders (timezone) | backend/models/reminder.py | ✅ |
| 8 | "Error cargando clientes" sin detalle | dragofactu_complete.py:2815 | ✅ |

#### Lo Que Funciona Bien
- Backend API completo (50+ endpoints, 52 tests)
- APIClient con todos los métodos necesarios
- Patrón híbrido en `refresh_data()` de tabs principales
- Dashboard stats endpoint funcionando
- DocumentDialog con save remoto
- ClientDialog y ProductDialog con modo híbrido
- Schemas y modelos correctos

---

### Sesión 2026-02-03: Fase 10 - Integración UI Híbrida
**AI Agent:** Claude Opus 4.5

#### Resumen
Completar la integración del modo híbrido (local/remoto) en la UI de Dragofactu.

#### Problema Detectado
Después de conectar al servidor Railway, el Dashboard y otras tabs seguían mostrando datos locales.

#### Solución Implementada

**1. Nuevo endpoint `/api/v1/dashboard/stats`**
- Archivo: `backend/app/api/v1/dashboard.py`
- Devuelve estadísticas agregadas

**2. APIClient actualizado**
- Nuevo método: `get_dashboard_stats()` → GET /dashboard/stats

**3. Dashboard híbrido**
- Métodos actualizados: `get_client_count()`, `get_product_count()`, `get_document_count()`, etc.
- Cache de stats con `_get_remote_stats()` y `_invalidate_stats_cache()`

**4. DocumentManagementTab híbrido**
- Refactorizado `refresh_data()` en tres métodos
- Nuevos métodos: `generate_pdf_by_id()`, `delete_document_by_id()`

**5. DocumentSummary schema actualizado**
- Añadido campo `client_name` para mostrar nombre de cliente en listas

#### Estado de Tabs
| Tab | Modo Local | Modo Remoto |
|-----|------------|-------------|
| Dashboard | ✅ | ✅ |
| Clientes | ✅ | ✅ |
| Productos | ✅ | ✅ |
| Documentos | ✅ | ✅ |
| Inventario | ✅ | ✅ |
| Diario | ✅ | ✅ |
| Trabajadores | ✅ | ✅ |

---

### Sesión 2026-02-02: Migración Multi-Tenant API
**AI Agent:** Claude Opus 4.5
**Duración:** Sesión completa de implementación

#### Fases Completadas

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

**Fase 6: APIClient Desktop**
- Clase APIClient completa
- Métodos para todos los endpoints
- Manejo de tokens y refresh
- Singleton para acceso global

#### Commits
```
fb477b6 - feat: Fase 1 - Setup inicial backend multi-tenant
bcca59d - feat: Fase 2 - Modelos y schemas completos con multi-tenancy
7c2d31e - feat: Fase 3 - Sistema de autenticacion JWT completo
9658b57 - feat: Fase 4 - CRUD endpoints completos
956ddde - feat: Fase 5 - Documents e inventario completo
6b9d920 - feat: Fase 6 - APIClient para cliente desktop
```

#### Decisiones Técnicas
1. **SQLite para desarrollo** en lugar de Docker/PostgreSQL (simplicidad)
2. **GUID type portable** para UUIDs (funciona en SQLite y PostgreSQL)
3. **bcrypt directo** en lugar de passlib (compatibilidad)
4. **Códigos con año:** PRE-2026-00001 para reinicio anual
5. **Soft delete:** is_active=False para mantener historial

---

### Sesión 2026-02-02: Deployment Railway
**Estado:** ✅ Backend desplegado y funcionando

#### Problema y Solución
- **Problema:** Railway build OK pero healthcheck fallaba
- **Causa:** Dockerfile usaba exec form que no expande $PORT
- **Solución:** Cambiar a shell form: `CMD /bin/sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"`

#### Configuración Railway
- Root Directory: `/backend`
- Branch: `main`
- Build: Dockerfile
- Healthcheck: `/health` (timeout 60s)

---

### Sesión 2026-02-01: Mejoras Documentos, Estados y Recordatorios
**AI Agent:** Claude Opus 4.5

#### Completado
- Nuevos Estados: `NOT_SENT`, `PARTIALLY_PAID`, `CANCELLED`
- Sistema de Traducción de Estados
- Filtro por Estado en DocumentManagementTab
- Filtro Ordenar Por
- DocumentDialog Mejorado (modo edición, selector cantidad, tabla editable)
- Código Clickeable
- Deducción Automática de Stock
- Sistema de Recordatorios completo
- Dashboard Mejorado (Documentos Pendientes + Recordatorios)

#### Patrones Importantes
```python
# Conversión UUID obligatoria
doc_id = self.document_id
if isinstance(doc_id, str):
    doc_id = uuid.UUID(doc_id)

# Traducción de estados
status_text = get_status_label(doc.status)
status_value = get_status_value("Pagado")

# Estados pendientes
pending_statuses = [DocumentStatus.DRAFT, DocumentStatus.SENT, ...]
```

---

### Sesión 2026-02-01: Configuración PDF Personalizable
**AI Agent:** Claude Opus 4.5

#### Completado
- Sistema de Configuración PDF Persistente (`PDFSettingsManager`)
- Datos de Empresa Personalizables
- Logo de Empresa (selector, vista previa, copiado)
- Texto de Pie de Factura Personalizable
- SettingsDialog Rediseñado (3 pestañas)
- InvoicePDFGenerator Actualizado

#### Ubicación de Archivos
- Config: `~/.dragofactu/pdf_settings.json`
- Logo: `~/.dragofactu/company_logo.png`

---

### Sesión 2026-01-31: Sistema de Traducción Completo
**AI Agent:** Claude (opencode)

#### Completado
- Sistema Core de Traducción Enhanced
- Traducción de Todas las Tabs
- Métodos retranslate_ui() en cada clase
- Archivos de Traducción Completos (es/en/de)

#### Características
- Cambio de Idioma en Vivo
- Persistencia de Preferencia
- Soporte de Claves Anidadas
- 100+ elementos UI traducibles

---

### Sesión 2026-01-13: Rediseño UI
**Archivo:** `docs/session-2026-01-13-ui-redesign.md`

#### Completado
- Sistema de diseño centralizado (`dragofactu/ui/styles.py`)
- Clase `UIStyles` en `dragofactu_complete.py`
- Dashboard con métricas, quick actions, documentos recientes
- MainWindow con menús limpios, tabs estilizados, status bar
- LoginDialog con layout card-based
- Menús sin emojis + shortcuts

---

### V1.0.0.4: Estabilización Crítica
**Archivo:** `STABILIZATION_COMPLETE.md`

- Import error `Product` en `inventory_service.py:266` - RESUELTO
- Syntax error try/except en `start_fixed.py` - RESUELTO
- Seguridad: credenciales env-based, JWT auto-generado - RESUELTO
- Arquitectura: launcher unificado `launch_dragofactu.py` - RESUELTO

---

### V1.0.0.2: DetachedInstanceError Fix
- Pre-extracción de datos de usuario en LoginDialog mientras sesión activa
- Uso de diccionario en lugar de objeto ORM desconectado

---

## Sistema de Diseño UI

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

### Métodos UIStyles
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
1. No emojis en botones o menús
2. Un solo color accent (#007AFF) para elementos interactivos
3. Bordes sutiles (1px gris claro)
4. Whitespace generoso (24-32px margins)
5. Headers tabla uppercase con color secundario
6. Ocultar grid lines en tablas, usar bottom borders
7. Hover states en elementos interactivos
8. Keyboard shortcuts para acciones comunes

---

## Modelos de Datos

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

## Arquitectura de Servicios

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

## Migración Multi-Tenant API - Detalles

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
│   ├── api/
│   │   ├── deps.py          # get_db, get_current_user, require_permission
│   │   ├── router.py        # Router principal
│   │   └── v1/              # 9 routers
│   └── core/
│       └── security.py      # hash_password, verify_password, JWT tokens
├── alembic/
├── tests/                   # 52 tests
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
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
POST /api/v1/documents/{id}/change-status
POST /api/v1/documents/{id}/convert
GET  /api/v1/documents/stats/summary

# Reminders (extra)
POST /api/v1/reminders/{id}/complete

# Dashboard
GET  /api/v1/dashboard/stats
```

### Lógica de Negocio Implementada
- Códigos automáticos: `PRE-2026-00001`, `FAC-2026-00001`, `ALB-2026-00001`
- Cálculos: subtotal, IVA 21%, total
- Transiciones de estado validadas: DRAFT→NOT_SENT→SENT→ACCEPTED→PAID
- Deducción stock: Al marcar factura como PAID
- Multi-tenancy: Todas las queries filtradas por company_id
- Permisos RBAC: admin, management, warehouse, read_only

### Testing (52 tests)
```bash
cd backend
source venv/bin/activate
python -m pytest tests/ -v
```

### Deployment Railway

**Configuración:**
- Root Directory: `/backend`
- Branch: `main`
- Build: Dockerfile
- Healthcheck: `/health`

**Variables de entorno REQUERIDAS:**
```bash
DATABASE_URL=postgresql://user:pass@host:5432/dbname
SECRET_KEY=<generar-32-chars-aleatorios>
DEBUG=false
ALLOWED_ORIGINS=http://localhost,https://tuapp.com
```

**Generar SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Fases Futuras - Guías Paso a Paso

### FASE 11: CONFIGURAR POSTGRESQL EN RAILWAY

**Objetivo:** Usar PostgreSQL en lugar de SQLite para persistencia real.

#### Paso 11.1: Añadir PostgreSQL en Railway
1. En Railway dashboard, click "New" → "Database" → "PostgreSQL"
2. Railway crea automáticamente la variable `DATABASE_URL`
3. Conectar el servicio backend al PostgreSQL

#### Paso 11.2: Verificar configuración
El código ya soporta PostgreSQL. Verificar que `backend/app/config.py` usa:
```python
DATABASE_URL: str = "sqlite:///./dragofactu_api.db"  # Default para dev
```
En Railway, la variable `DATABASE_URL` del PostgreSQL sobreescribe este default.

#### Paso 11.3: Migrar datos (si hay)
```bash
python -c "
from app.database import engine
from app.models.base import Base
Base.metadata.create_all(bind=engine)
print('Tables created')
"
```

---

### FASE 12: REGISTRO DE EMPRESA (ONBOARDING)

**Objetivo:** Permitir que nuevos usuarios creen su empresa.

#### Paso 12.1: Crear OnboardingDialog

```python
class OnboardingDialog(QDialog):
    """Diálogo para registro de nueva empresa."""

    def __init__(self, server_url, parent=None):
        super().__init__(parent)
        self.server_url = server_url
        self.setWindowTitle("Registrar Nueva Empresa")
        self.setMinimumSize(500, 600)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Datos de empresa
        company_group = QGroupBox("Datos de la Empresa")
        company_layout = QFormLayout()

        self.company_name = QLineEdit()
        self.company_tax_id = QLineEdit()
        self.company_tax_id.setPlaceholderText("B12345678")
        # ... resto de campos

        # Datos de admin
        admin_group = QGroupBox("Usuario Administrador")
        # ... campos de usuario

        # Botones
        self.register_btn = QPushButton("Registrar")
        self.register_btn.clicked.connect(self.register)

    def register(self):
        from dragofactu.services.api_client import get_api_client
        client = get_api_client(self.server_url)
        result = client.register(...)
```

---

### FASE 13: SINCRONIZACIÓN Y MODO OFFLINE

**Objetivo:** Permitir trabajo offline con sincronización posterior.

#### Paso 13.1: Cache local de datos

```python
class LocalCache:
    """Cache local para modo offline."""

    def __init__(self):
        self.cache_dir = Path.home() / ".dragofactu" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def save_clients(self, clients: list):
        with open(self.cache_dir / "clients.json", "w") as f:
            json.dump(clients, f)

    def load_clients(self) -> list:
        cache_file = self.cache_dir / "clients.json"
        if cache_file.exists():
            with open(cache_file) as f:
                return json.load(f)
        return []
```

#### Paso 13.2: Cola de operaciones pendientes

```python
class OperationQueue:
    """Cola de operaciones para sincronizar cuando haya conexión."""

    def __init__(self):
        self.queue_file = Path.home() / ".dragofactu" / "pending_operations.json"
        self.operations = self._load()

    def add(self, operation_type: str, entity_type: str, data: dict):
        self.operations.append({
            "type": operation_type,
            "entity": entity_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
        self._save()

    def sync(self, api_client):
        """Sincronizar operaciones pendientes."""
        synced = []
        for op in self.operations:
            try:
                if op["type"] == "create":
                    if op["entity"] == "client":
                        api_client.create_client(**op["data"])
                synced.append(op)
            except Exception as e:
                print(f"Error syncing {op}: {e}")

        self.operations = [op for op in self.operations if op not in synced]
        self._save()
```

---

### FASE 14: TESTING DE INTEGRACIÓN

**Objetivo:** Asegurar que todo funciona end-to-end.

#### Tests manuales a realizar:

1. **Login remoto:**
   - [ ] Configurar URL del servidor en Settings
   - [ ] Login con credenciales válidas
   - [ ] Login con credenciales inválidas
   - [ ] Token refresh automático

2. **CRUD via API:**
   - [ ] Crear cliente → aparece en tabla
   - [ ] Editar cliente → cambios guardados
   - [ ] Eliminar cliente → desaparece (soft delete)
   - [ ] Repetir para productos, documentos, etc.

3. **Documentos:**
   - [ ] Crear presupuesto
   - [ ] Convertir a factura
   - [ ] Cambiar estado a PAID
   - [ ] Verificar stock descontado

4. **Multi-tenant:**
   - [ ] Registrar 2 empresas diferentes
   - [ ] Verificar que datos están aislados

---

## TODOs Pendientes en Código

```
dragofactu/ui/views/dashboard_view.py:173    # TODO: Implement unpaid invoices
dragofactu/ui/views/dashboard_view.py:195    # TODO: Implement activity logging
dragofactu/ui/views/documents_view.py:19     # TODO: Implement documents table
dragofactu/ui/views/clients_view.py:19       # TODO: Implement clients table
```

---

## Plan de Migración Original

> El contenido original del plan de migración se encuentra en el archivo `pasos a seguir migracion.md`.
> Incluye:
> - Arquitectura detallada (actual vs objetivo)
> - Cambios en Base de Datos
> - Modelo Company (Tenant)
> - Estrategia de Multi-Tenancy (Row-Level Security)
> - Estructura de carpetas Backend
> - Configuración FastAPI
> - Migraciones Alembic

Para ver el plan completo original, consultar: `pasos a seguir migracion.md`

---

## Documentación Adicional

- `docs/UI_DESIGN_SYSTEM.md` - Sistema de diseño completo con CSS/QSS
- `docs/session-2026-01-13-ui-redesign.md` - Log sesión rediseño UI
- `STABILIZATION_COMPLETE.md` - Resumen fixes v1.0.0.4
- `README_FINAL.md` - Estado funcional completo
- `pasos a seguir migracion.md` - Plan de migración detallado original
