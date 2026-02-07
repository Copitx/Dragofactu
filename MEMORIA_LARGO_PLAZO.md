# MEMORIA_LARGO_PLAZO.md

> **Este archivo contiene el historial completo del proyecto Dragofactu.**
> Para el contexto operativo esencial, ver `CLAUDE.md`.
>
> Última actualización: 2026-02-07

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
| v2.1.0 | 2026-02-07 | Fase 13: Cache offline + cola operaciones + monitor conectividad |
| v2.2.0 | 2026-02-07 | Fases 14-15: Testing completo (103 tests) + Seguridad + CI/CD |
| v2.3.0 | 2026-02-07 | Fase 16: Export/Import CSV, Audit Log, Financial Reports (130 tests) |

---

## Sesiones de Desarrollo por Fecha

### Sesión 2026-02-07: Fase 13 - Cache Offline y Sincronización
**AI Agent:** Claude Opus 4.6

#### Resumen
Implementación completa de Fase 13: sistema de cache offline con cola de operaciones pendientes y detección de conectividad.

#### Componentes Creados

**1. `dragofactu/services/offline_cache.py`** - Módulo central
- **LocalCache**: Cache JSON en `~/.dragofactu/cache/` con TTL configurable
  - Cachea: clients, products, documents, workers, diary, suppliers, reminders, dashboard_stats
  - Métodos: save(), load(), clear(), has_cache(), get_cache_age()
- **OperationQueue**: Cola de operaciones write (create/update/delete) pendientes
  - Persistida en `~/.dragofactu/pending_operations.json`
  - Sync automático al recuperar conexión
  - 3 reintentos máximo por operación
- **ConnectivityMonitor**: Detección online/offline
  - Listeners para cambios de estado
  - Auto-sync al volver online

**2. Modificaciones en `api_client.py`**
- `_request()` ahora cachea respuestas GET exitosas automáticamente
- En ConnectionError/Timeout para GET: devuelve datos cacheados con flag `_from_cache=True`
- ConnectivityMonitor se actualiza en cada request

**3. Integración UI en `dragofactu_complete.py`**
- Status bar: indicador de conectividad ("En linea" / "Sin conexion (cache)")
- Status bar: contador de operaciones pendientes
- Menu Herramientas: "Sincronizar pendientes" (Ctrl+Shift+S) y "Limpiar cache"
- Todas las tabs: muestran "(cache - sin conexion)" cuando datos vienen de cache
- Dashboard: indicador de datos cacheados en subtítulo

**4. Traducciones**
- `menu.sync` y `menu.clear_cache` en es/en/de

#### Archivos Modificados
| Archivo | Cambios |
|---------|---------|
| `dragofactu/services/offline_cache.py` | NUEVO - 300+ líneas |
| `dragofactu/services/api_client.py` | Cache integrado en _request() |
| `dragofactu_complete.py` | Status bar, menú sync, indicadores cache en tabs |
| `dragofactu/config/translations/es.json` | +2 claves menu |
| `dragofactu/config/translations/en.json` | +2 claves menu |
| `dragofactu/config/translations/de.json` | +2 claves menu |
| `CLAUDE.md` | Actualizado con Fase 13 |

#### Notas Técnicas
- Cache sin límite de edad cuando offline (`max_age=0`)
- Flag `_from_cache` en response dict permite a la UI detectar datos cacheados
- ConnectivityMonitor es thread-safe con threading.Lock
- Usa QMetaObject.invokeMethod para callbacks thread-safe en Qt

---

### Sesión 2026-02-07 (4): Fase 16 - Features Backend
**AI Agent:** Claude Opus 4.6

#### Resumen
Implementación de tres nuevas funcionalidades backend: export/import CSV, audit log, e informes financieros. 27 tests nuevos (103 → 130).

#### Componentes Creados

**1. Export/Import CSV (`backend/app/api/v1/export_import.py`)**
- Export CSV para: clients, products, suppliers
- Import CSV para: clients, products
- Detección de duplicados (skip por code), validación de campos obligatorios
- Soporte UTF-8 y Latin-1 fallback
- Multi-tenancy: solo exporta/importa datos de la empresa autenticada

**2. Audit Log (`backend/app/models/audit_log.py` + `backend/app/api/v1/audit.py`)**
- Modelo AuditLog: company_id, user_id, action, entity_type, entity_id, details (JSON)
- Endpoint GET /api/v1/audit con filtros por action y entity_type
- Helper `log_action()` para usar desde otros endpoints
- Paginación y multi-tenancy

**3. Financial Reports (`backend/app/api/v1/reports.py`)**
- GET /api/v1/reports/monthly?year=&month=
- GET /api/v1/reports/quarterly?year=&quarter=
- GET /api/v1/reports/annual?year= (12 meses desglosados)
- Totales: invoiced, paid, pending, quotes, por tipo de documento

**4. Schemas (`backend/app/schemas/audit_log.py` + `backend/app/schemas/report.py`)**
- AuditLogResponse, AuditLogList
- PeriodReport, DocumentTypeSummary, AnnualReport

#### Tests Nuevos (27 tests)
| Archivo | Tests | Cobertura |
|---------|-------|-----------|
| `test_export_import.py` | 12 | Export CSV (empty, data, unauthorized, multi-tenancy), Import (success, duplicates, invalid file, missing fields) |
| `test_audit.py` | 7 | List (empty, data, pagination, filter action, filter entity), unauthorized, multi-tenancy |
| `test_reports.py` | 8 | Monthly (empty, data), quarterly, annual, unauthorized, invalid params, multi-tenancy |

#### Archivos Creados/Modificados
| Archivo | Cambios |
|---------|---------|
| `backend/app/models/audit_log.py` | NUEVO - Modelo AuditLog |
| `backend/app/schemas/audit_log.py` | NUEVO - Schemas audit |
| `backend/app/schemas/report.py` | NUEVO - Schemas reports |
| `backend/app/api/v1/export_import.py` | NUEVO - Export/Import endpoints |
| `backend/app/api/v1/audit.py` | NUEVO - Audit log endpoint + helper |
| `backend/app/api/v1/reports.py` | NUEVO - Financial reports |
| `backend/app/models/__init__.py` | + AuditLog |
| `backend/app/schemas/__init__.py` | + audit_log, report schemas |
| `backend/app/api/router.py` | + 3 nuevos routers |
| `backend/tests/test_export_import.py` | NUEVO - 12 tests |
| `backend/tests/test_audit.py` | NUEVO - 7 tests |
| `backend/tests/test_reports.py` | NUEVO - 8 tests |

---

### Sesión 2026-02-07 (3): Fase 15 - Seguridad + CI/CD
**AI Agent:** Claude Opus 4.6

#### Resumen
Hardening de seguridad del backend y pipeline de integración continua.

#### Cambios Implementados

**1. CORS Configurable (`config.py` + `main.py`)**
- `ALLOWED_ORIGINS` ahora es string en config (comma-separated)
- Nuevo método `get_cors_origins()` para parsear a lista
- En producción, establecer `ALLOWED_ORIGINS=https://tuapp.com,http://localhost`

**2. Validación de Inputs en Schemas (8 archivos)**
- Añadido `max_length` a 15+ campos que no tenían límite:
  - `address`: max 500 chars (client, supplier, worker)
  - `notes`: max 2000 chars (client, supplier, reminder)
  - `description`: max 2000 chars (product, worker course, reminder)
  - `content` (diary): max 50000 chars
  - `tags` (diary): max 500 chars
  - `notes/internal_notes/terms` (document): max 5000 chars
  - `description` (document line): max 500 chars
  - `password` (auth): max 128 chars

**3. Middleware Stack (`main.py`)**
- `RequestLoggingMiddleware`: Log de cada request con método, path, status y duración
- `RequestSizeLimitMiddleware`: Rechaza requests > 10MB (configurable via `MAX_REQUEST_SIZE`)
- Logging migrado de `print()` a `logging` module con formato estructurado

**4. GitHub Actions CI (`.github/workflows/test.yml`)**
- Ejecuta 103 tests en push/PR a main (solo si cambian archivos en `backend/`)
- Python 3.11, pip cache, SQLite in-memory para tests

**5. Rate Limiting (ya existía)**
- Login: 5 intentos / 5 minutos por IP
- Register: 3 intentos / 1 hora por IP
- Implementado en `security_utils.py` con threading.Lock

#### Archivos Modificados
| Archivo | Cambios |
|---------|---------|
| `backend/app/config.py` | ALLOWED_ORIGINS como string, get_cors_origins(), MAX_REQUEST_SIZE |
| `backend/app/main.py` | 2 nuevos middlewares, logging estructurado |
| `backend/app/schemas/client.py` | max_length en address, notes |
| `backend/app/schemas/supplier.py` | max_length en address, notes |
| `backend/app/schemas/product.py` | max_length en description |
| `backend/app/schemas/worker.py` | max_length en address, description |
| `backend/app/schemas/diary.py` | max_length en content, tags |
| `backend/app/schemas/reminder.py` | max_length en description |
| `backend/app/schemas/document.py` | max_length en description, notes, terms |
| `backend/app/schemas/auth.py` | max_length en password |
| `.github/workflows/test.yml` | NUEVO - CI pipeline |

---

### Sesión 2026-02-07 (2): Fase 14 - Testing Completo + TODOs Resueltos
**AI Agent:** Claude Opus 4.6

#### Resumen
Testing completo del backend (de 52 a 103 tests) y resolución de todos los TODOs pendientes en el código.

#### Tests Nuevos (51 tests)

| Archivo | Tests | Cobertura |
|---------|-------|-----------|
| `test_suppliers.py` | 12 | CRUD completo + búsqueda + paginación + multi-tenancy |
| `test_workers.py` | 13 | CRUD + filtro departamento + búsqueda + cursos + multi-tenancy |
| `test_diary.py` | 10 | CRUD + filtro pinned + multi-tenancy |
| `test_reminders.py` | 12 | CRUD + prioridad + pending_only + complete + multi-tenancy |
| `test_dashboard.py` | 4 | Stats vacío + con datos + unauthorized + multi-tenancy |

#### TODOs Resueltos

| TODO | Archivo | Solución |
|------|---------|----------|
| Unpaid Invoices count | `dashboard_view.py:173` | Query real: facturas con status SENT/ACCEPTED/NOT_SENT |
| Activity logging | `dashboard_view.py:195` | Muestra 5 documentos recientes con código, status y fecha |
| Clients placeholder | `clients_view.py:19` | Actualizado texto (legacy view, funcionalidad en monolítico) |
| Documents placeholder | `documents_view.py:19` | Actualizado texto (legacy view, funcionalidad en monolítico) |

#### Plan Detallado Fases 14-18
Se escribió roadmap completo (~450 líneas) en la sección "Fases Futuras" de este archivo con guías paso a paso para:
- Fase 14: Testing (✅ completada en esta sesión)
- Fase 15: Seguridad + CI/CD
- Fase 16: Features backend
- Fase 17: UI/UX
- Fase 18: Producción

---

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

### FASE 13: SINCRONIZACIÓN Y MODO OFFLINE ✅ COMPLETADA

**Implementado en v2.1.0 (2026-02-07)**

Ver sesión 2026-02-07 arriba para detalles completos.

**Archivos clave:**
- `dragofactu/services/offline_cache.py` - LocalCache, OperationQueue, ConnectivityMonitor
- `dragofactu/services/api_client.py` - Cache integrado en _request()
- `~/.dragofactu/cache/` - Directorio de cache JSON
- `~/.dragofactu/pending_operations.json` - Cola de operaciones

---

### FASE 14: TESTING COMPLETO (Backend + Integración) ✅ COMPLETADA

**Completado:** 2026-02-07 — 103 tests passing (51 nuevos).
**Tests de integración manual:** Pendientes para el usuario (ver checklist abajo).

#### Estado Actual de Tests

```
backend/tests/
├── conftest.py       # Fixtures: db, client, test_company, test_user, auth_headers
├── test_auth.py      # 13 tests ✅
├── test_clients.py   # 12 tests ✅
├── test_products.py  # ~12 tests ✅
├── test_documents.py # ~10 tests ✅
├── test_health.py    # ~5 tests ✅
```

**Tests que FALTAN (por orden de prioridad):**

#### Paso 14.1: Tests Suppliers (~8 tests)
```bash
# Crear: backend/tests/test_suppliers.py
```
Tests a implementar:
- [ ] `test_create_supplier` - POST /suppliers con datos válidos
- [ ] `test_list_suppliers` - GET /suppliers con paginación
- [ ] `test_get_supplier` - GET /suppliers/{id}
- [ ] `test_update_supplier` - PUT /suppliers/{id}
- [ ] `test_delete_supplier` - DELETE /suppliers/{id} (soft delete)
- [ ] `test_search_suppliers` - GET /suppliers?search=
- [ ] `test_supplier_multi_tenancy` - No ver suppliers de otra empresa
- [ ] `test_supplier_unauthenticated` - 401 sin token

#### Paso 14.2: Tests Workers (~8 tests)
```bash
# Crear: backend/tests/test_workers.py
```
- [ ] CRUD completo (create, list, get, update, delete)
- [ ] Filtro por departamento
- [ ] Búsqueda por nombre/código
- [ ] Multi-tenancy aislamiento

#### Paso 14.3: Tests Diary (~6 tests)
```bash
# Crear: backend/tests/test_diary.py
```
- [ ] CRUD entradas de diario
- [ ] Filtro por fecha
- [ ] Multi-tenancy

#### Paso 14.4: Tests Reminders (~8 tests)
```bash
# Crear: backend/tests/test_reminders.py
```
- [ ] CRUD reminders
- [ ] POST /reminders/{id}/complete
- [ ] Filtro por prioridad
- [ ] Filtro por estado (completado/pendiente)
- [ ] Timezone handling (problema que ya corregimos en v2.0.2)

#### Paso 14.5: Tests Dashboard (~4 tests)
```bash
# Crear: backend/tests/test_dashboard.py
```
- [ ] GET /dashboard/stats retorna formato correcto
- [ ] Stats reflejan datos reales (crear datos → verificar conteo)
- [ ] Multi-tenancy en stats

#### Paso 14.6: Tests Documentos Avanzados (~6 tests)
```bash
# Añadir a: backend/tests/test_documents.py
```
- [ ] `test_change_status_valid_transition` - DRAFT→SENT
- [ ] `test_change_status_invalid_transition` - PAID→DRAFT (debe fallar)
- [ ] `test_convert_quote_to_invoice` - POST /documents/{id}/convert
- [ ] `test_stock_deduction_on_paid` - Stock se descuenta al pagar
- [ ] `test_document_code_auto_generation` - Códigos PRE-/FAC-/ALB- automáticos
- [ ] `test_document_with_lines` - Documento con líneas de producto

#### Paso 14.7: Tests de Integración Desktop (Manuales)

Checklist manual para verificar flujo completo:

1. **Login remoto:**
   - [ ] Configurar URL servidor en Settings
   - [ ] Login con credenciales válidas
   - [ ] Login con credenciales inválidas → mensaje error
   - [ ] Token refresh automático (esperar >15min)

2. **CRUD via API (cada tab):**
   - [ ] Crear/Editar/Eliminar cliente
   - [ ] Crear/Editar/Eliminar producto
   - [ ] Crear/Editar/Eliminar documento
   - [ ] Crear/Editar/Eliminar trabajador
   - [ ] Crear/Editar/Eliminar nota diario

3. **Documentos avanzados:**
   - [ ] Crear presupuesto → convertir a factura
   - [ ] Cambiar estado a PAID → verificar stock descontado
   - [ ] Generar PDF

4. **Cache offline (Fase 13):**
   - [ ] Con servidor activo: datos se cachean automáticamente
   - [ ] Desconectar red: app muestra datos cacheados con indicador
   - [ ] Reconectar: operaciones pendientes se sincronizan
   - [ ] Limpiar cache → datos se borran

5. **Multi-tenant:**
   - [ ] Registrar 2 empresas diferentes
   - [ ] Verificar que datos están aislados

---

### FASE 15: SEGURIDAD Y CI/CD ✅ COMPLETADA

**Completado:** 2026-02-07 — CORS configurable, validación inputs, logging, CI pipeline.
**Prioridad:** ALTA - Requisito antes de aceptar usuarios reales.

#### Paso 15.1: CORS Restrictivo

**Archivo:** `backend/app/main.py`

Actualmente CORS está abierto (`allow_origins=["*"]`). Restringir:

```python
# Cambiar de:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ← PELIGROSO
)

# A:
ALLOWED_ORIGINS = settings.ALLOWED_ORIGINS.split(",") if settings.ALLOWED_ORIGINS else ["http://localhost"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

**Verificar:** Variable `ALLOWED_ORIGINS` en Railway settings.

#### Paso 15.2: Validación de Inputs

**Archivos:** `backend/app/schemas/*.py`

Añadir límites de longitud y validación a todos los schemas:

```python
from pydantic import Field, validator

class ClientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    tax_id: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=254)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
```

Aplicar patrón similar a: ProductCreate, DocumentCreate, WorkerCreate, SupplierCreate.

#### Paso 15.3: Rate Limiting

**Archivo:** `backend/app/main.py`

Añadir rate limiting básico para login:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# En auth router:
@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, ...):
    ...
```

**Dependencia nueva:** `slowapi` en requirements.txt

#### Paso 15.4: GitHub Actions CI

**Archivo nuevo:** `.github/workflows/test.yml`

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ./backend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pip install pytest httpx
      - run: python -m pytest tests/ -v --tb=short
```

#### Paso 15.5: Logging Estructurado

**Archivo:** `backend/app/main.py` + `backend/app/core/logging.py`

Añadir logging con formato JSON para Railway:

```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        })

# Middleware para log de requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    logger.info(f"{request.method} {request.url.path} → {response.status_code} ({duration:.2f}s)")
    return response
```

---

### FASE 16: FUNCIONALIDADES BACKEND PENDIENTES ✅ COMPLETADA

**Objetivo:** Completar funcionalidades del backend que la UI espera pero no existen.
**Prioridad:** MEDIA - Mejoras incrementales.
**Estado:** ✅ Completada (2026-02-07) - 27 tests nuevos, total 130.

#### Paso 16.1: Exportar/Importar Datos

**Endpoints nuevos:**

```
GET  /api/v1/export/clients?format=csv     # Exportar clientes a CSV
GET  /api/v1/export/products?format=csv    # Exportar productos a CSV
POST /api/v1/import/clients                # Importar desde CSV
POST /api/v1/import/products               # Importar desde CSV
```

**Archivos a crear:**
- `backend/app/api/v1/export_import.py` - Router con endpoints
- Usar `csv` stdlib para generación
- `StreamingResponse` para archivos grandes

**Integración Desktop:**
- Menú Archivo → Importar / Exportar ya existe en la UI
- Conectar acciones del menú a diálogos de selección de archivo
- Llamar a nuevos endpoints del APIClient

#### Paso 16.2: Audit Log (Registro de Auditoría)

**Objetivo:** Registrar quién hizo qué y cuándo.

**Modelo nuevo:** `backend/app/models/audit_log.py`

```python
class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    company_id = Column(GUID(), ForeignKey("companies.id"))
    user_id = Column(GUID(), ForeignKey("users.id"))
    action = Column(String(50))  # CREATE, UPDATE, DELETE, LOGIN, STATUS_CHANGE
    entity_type = Column(String(50))  # client, product, document, etc.
    entity_id = Column(GUID(), nullable=True)
    details = Column(Text, nullable=True)  # JSON con cambios
    created_at = Column(DateTime, default=func.now())
```

**Middleware o servicio:**
```python
def log_action(db, user, action, entity_type, entity_id=None, details=None):
    entry = AuditLog(
        company_id=user.company_id,
        user_id=user.id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=json.dumps(details) if details else None,
    )
    db.add(entry)
    db.commit()
```

**Endpoint:** GET /api/v1/audit-log?entity_type=&limit=&offset=

#### Paso 16.3: Generación de Informes

**Objetivo:** Endpoint que genera resúmenes financieros.

```
GET /api/v1/reports/monthly?year=2026&month=2
GET /api/v1/reports/quarterly?year=2026&quarter=1
GET /api/v1/reports/annual?year=2026
```

**Respuesta:**
```json
{
  "period": "2026-02",
  "total_invoiced": 15000.00,
  "total_paid": 12000.00,
  "total_pending": 3000.00,
  "num_invoices": 15,
  "num_quotes": 8,
  "top_clients": [...],
  "top_products": [...]
}
```

**Integración Desktop:**
- Tab Reports (menú ya existe, tab no implementada)
- Mostrar tablas y gráficos con datos del endpoint

---

### FASE 17: MEJORAS UI/UX

**Objetivo:** Pulir la experiencia de usuario del desktop.
**Prioridad:** MEDIA-BAJA - Mejoras de calidad de vida.

#### Paso 17.1: Tema Oscuro

**Archivo:** `dragofactu/ui/styles.py` + `dragofactu_complete.py`

Añadir paleta oscura a UIStyles:

```python
class UIStyles:
    _dark_mode = False

    DARK_COLORS = {
        "bg_app": "#1C1C1E",
        "bg_card": "#2C2C2E",
        "bg_hover": "#3A3A3C",
        "text_primary": "#FFFFFF",
        "text_secondary": "#AEAEB2",
        "text_tertiary": "#636366",
        "accent": "#0A84FF",
        "border": "#48484A",
        "border_light": "#38383A",
    }
```

- Toggle en Settings → Apariencia → Tema: Claro/Oscuro
- Persistir en `~/.dragofactu/app_mode.json`
- Todos los métodos `get_*_style()` verifican `_dark_mode`

#### Paso 17.2: Atajos de Teclado Mejorados

Atajos globales adicionales:
| Atajo | Acción |
|-------|--------|
| `Ctrl+1` a `Ctrl+7` | Cambiar a tab 1-7 |
| `Ctrl+F` | Focus en barra de búsqueda |
| `Ctrl+N` | Nuevo elemento (según tab activa) |
| `Escape` | Cerrar diálogo/limpiar búsqueda |
| `F5` | Refrescar datos |

#### Paso 17.3: Notificaciones en App

Reemplazar `QMessageBox` por notificaciones tipo toast:

```python
class ToastNotification(QWidget):
    """Notificación flotante no-intrusiva."""
    def __init__(self, message, type="success", parent=None):
        # Animación slide-in desde la esquina superior derecha
        # Auto-cerrar en 3 segundos
        # Tipos: success (verde), warning (amarillo), error (rojo), info (azul)
```

#### Paso 17.4: Mejoras en Tablas

- Ordenación clickeando en headers (sort ASC/DESC)
- Columnas redimensionables con persistencia
- Doble-click para editar
- Selección múltiple + eliminación masiva
- Exportar selección a CSV

---

### FASE 18: PRODUCCIÓN Y MONITOREO

**Objetivo:** Preparar para uso real con múltiples empresas.
**Prioridad:** BAJA - Solo cuando haya usuarios reales.

#### Paso 18.1: Health Check Avanzado

```python
@app.get("/health")
async def health(db: Session = Depends(get_db)):
    return {
        "status": "healthy",
        "version": "2.1.0",
        "database": "connected",  # Verificar conexión real
        "uptime": get_uptime(),
        "active_companies": db.query(Company).count(),
    }
```

#### Paso 18.2: Backup Automático

Script de backup para Railway PostgreSQL:

```bash
#!/bin/bash
# backup.sh - Ejecutar con cron o Railway scheduled job
pg_dump $DATABASE_URL | gzip > backup_$(date +%Y%m%d).sql.gz
# Subir a S3 o similar
```

#### Paso 18.3: Migración Alembic Automatizada

Configurar Alembic para migraciones automáticas en deploy:

```python
# backend/app/main.py - en lifespan
from alembic.config import Config
from alembic import command

async def lifespan(app: FastAPI):
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    yield
```

#### Paso 18.4: Métricas y Alertas

- Endpoint `/metrics` con formato Prometheus
- Métricas: requests/s, latencia, errores, usuarios activos
- Alertas: error rate > 5%, latencia > 2s

#### Paso 18.5: Documentación API

- Swagger UI ya viene con FastAPI (`/docs`)
- Añadir descripciones detalladas a cada endpoint
- Generar página de documentación para clientes API

---

### Resumen de Prioridades

| Fase | Prioridad | Dependencias | Impacto |
|------|-----------|--------------|---------|
| **14: Testing** | ✅ COMPLETADA | - | 103 tests passing |
| **15: Seguridad + CI** | ✅ COMPLETADA | - | CORS, validación, logging, CI |
| **16: Features Backend** | 🟡 MEDIA | Fase 15 | Funcionalidad completa |
| **17: UI/UX** | 🟢 MEDIA-BAJA | Ninguna | Calidad de vida |
| **18: Producción** | 🔵 BAJA | Fases 14-16 | Solo con usuarios reales |

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
