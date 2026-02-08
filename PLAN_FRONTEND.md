# PLAN_FRONTEND.md - Frontend Web Dragofactu (Fases 19-25)

> **Última actualización:** 2026-02-08
> **Estado general:** Fases 19-21 completadas, Fase 22 siguiente

---

## Resumen de Estado

| Fase | Descripción | Estado | Fecha |
|------|-------------|--------|-------|
| 19 | Scaffolding + Auth + Routing | ✅ Completada | 2026-02-08 |
| 20 | Layout + Dashboard | ✅ Completada | 2026-02-08 |
| 21 | CRUD Clientes/Productos/Proveedores | ✅ Completada | 2026-02-08 |
| **22** | **Documentos (line editor, status, PDF)** | **⬜ SIGUIENTE** | - |
| 23 | Inventario, Workers, Diary, Reminders | ⬜ Pendiente | - |
| 24 | Reports, Export/Import, Audit, Admin, Settings | ⬜ Pendiente | - |
| 25 | PWA + Mobile + Deploy + Testing | ⬜ Pendiente | - |

---

## Decisiones Arquitectónicas

| Decisión | Elección | Razón |
|----------|----------|-------|
| Framework | React 18 + TypeScript | Ecosistema maduro, type safety |
| Build tool | Vite 5 | Rápido, configuración mínima |
| UI components | shadcn/ui + TailwindCSS | Accesibles, personalizables |
| API state | TanStack Query v5 | Cache, dedup, retry, offline |
| Client state | Zustand | Solo auth/theme/locale |
| Forms | react-hook-form + zod | Validación type-safe |
| Routing | React Router v7 | SPA, lazy loading |
| i18n | react-i18next | Mismas claves que desktop |
| Charts | Recharts | Dashboard gráficas |
| Deploy | Single service Railway | FastAPI sirve static + API |

---

## Qué YA EXISTE (Fases 19-20 completadas)

### Archivos creados y funcionales

**Config/Build:**
- `frontend/package.json` - Dependencias instaladas
- `frontend/vite.config.ts` - Proxy API → Railway production
- `frontend/tailwind.config.ts` - Paleta Dragofactu con CSS vars
- `frontend/tsconfig.json` - Strict mode, path aliases @/
- `frontend/postcss.config.js`
- `frontend/index.html`
- `frontend/.gitignore` - node_modules, dist

**API Layer:**
- `src/api/client.ts` - Axios instance + refresh token interceptor
- `src/api/auth.ts` - login, register, getMe, logout
- `src/api/dashboard.ts` - getDashboardStats

**Stores (Zustand persist):**
- `src/stores/auth-store.ts` - tokens, user, isAuthenticated
- `src/stores/ui-store.ts` - theme, locale, sidebarCollapsed

**Types:**
- `src/types/auth.ts` - LoginRequest, UserResponse, etc.
- `src/types/common.ts` - PaginatedResponse, MessageResponse

**i18n (completo para toda la app):**
- `src/i18n/index.ts` - react-i18next config
- `src/i18n/es.json` - Todas las claves (auth, nav, clients, products, suppliers, documents, inventory, workers, diary, reminders, reports, settings, admin, buttons, common)
- `src/i18n/en.json` - Ídem en inglés
- `src/i18n/de.json` - Ídem en alemán

**Layout Components:**
- `src/components/layout/app-layout.tsx` - Sidebar + content + mobile nav
- `src/components/layout/sidebar.tsx` - Nav lateral colapsable, activo highlight
- `src/components/layout/header.tsx` - Título + user menu + theme + language
- `src/components/layout/mobile-nav.tsx` - Bottom tabs + overlay menu

**Common Components:**
- `src/components/common/metric-card.tsx` - Card con icono y variantes de color
- `src/components/common/loading.tsx` - Spinner, PageSkeleton, TableSkeleton
- `src/components/common/empty-state.tsx` - Icono + título + descripción

**UI Components (shadcn/ui pattern):**
- `src/components/ui/button.tsx` - Variants: default, destructive, outline, secondary, ghost, link
- `src/components/ui/input.tsx`
- `src/components/ui/label.tsx`
- `src/components/ui/card.tsx`
- `src/components/ui/dialog.tsx`
- `src/components/ui/select.tsx`
- `src/components/ui/dropdown-menu.tsx`

**Utility Components:**
- `src/components/theme-toggle.tsx` - Light/Dark/System
- `src/components/language-selector.tsx` - ES/EN/DE

**Pages:**
- `src/pages/auth/login.tsx` - Form con react-hook-form + zod
- `src/pages/auth/register.tsx` - Registro empresa + admin, auto-login
- `src/pages/dashboard.tsx` - 6 metric cards con datos API reales
- `src/pages/not-found.tsx` - 404
- `src/pages/placeholder.tsx` - Placeholder para rutas no implementadas

**Hooks:**
- `src/hooks/use-dashboard.ts` - useQuery para stats

**Main:**
- `src/main.tsx` - React root + i18n + CSS
- `src/App.tsx` - Router, ProtectedRoute, PublicRoute, AppLayout, lazy loading
- `src/lib/utils.ts` - cn(), formatCurrency, formatDate
- `src/styles/globals.css` - Tailwind + CSS vars light/dark

### Archivos Fase 21 (integrados)
- `src/api/clients.ts`, `products.ts`, `suppliers.ts` - Funciones API completas
- `src/types/client.ts`, `product.ts`, `supplier.ts` - Interfaces TypeScript
- `src/components/data-table/data-table.tsx` - DataTable genérico reutilizable
- `src/components/data-table/toolbar.tsx` - Search + filters + add button
- `src/components/data-table/pagination.tsx` - Paginación con selector de filas
- `src/components/forms/confirm-dialog.tsx` - Confirmación de borrado
- `src/components/ui/table.tsx`, `badge.tsx`, `textarea.tsx` - shadcn/ui nuevos
- `src/lib/validators.ts` - Zod schemas (client, product, supplier, stockAdjustment)
- `src/hooks/use-clients.ts`, `use-products.ts`, `use-suppliers.ts` - TanStack Query hooks
- `src/pages/clients/index.tsx` - CRUD clientes completo
- `src/pages/products/index.tsx` - CRUD productos + ajuste stock
- `src/pages/suppliers/index.tsx` - CRUD proveedores completo
- App.tsx actualizado: /clients, /products, /suppliers enrutan a páginas reales

---

## FASE 21: CRUD - Clientes, Productos, Proveedores ✅ COMPLETADA

---

## FASE 22: Documentos (la más compleja)

### Objetivo
Gestión completa de documentos: listado con filtros, creación con editor de líneas, transiciones de estado, conversión y PDF.

### Archivos a crear
1. `src/pages/documents/index.tsx` - Lista con filtros tipo/estado/fecha
2. `src/pages/documents/new.tsx` - Formulario creación con line editor
3. `src/pages/documents/[id].tsx` - Detalle + acciones estado
4. `src/api/documents.ts` - Todos los endpoints
5. `src/hooks/use-documents.ts` - Query hooks
6. `src/types/document.ts` - Types completos
7. `src/components/document-editor/line-editor.tsx` - Editor líneas con cálculo automático
8. `src/components/document-editor/totals-panel.tsx` - Subtotal/IVA/Total
9. `src/components/document-editor/status-badge.tsx` - Badge coloreado por estado
10. `src/lib/constants.ts` - STATUS_TRANSITIONS, DOC_TYPES

### Editor de líneas
- Cada línea: producto_id, descripción, cantidad, precio, descuento %
- Cálculo automático: subtotal = qty * price * (1 - discount/100)
- Total = sum(subtotals), IVA = subtotal * 21%
- Botón + para añadir línea, X para eliminar
- Selector de producto rellena precio automáticamente

### Transiciones de estado
```
DRAFT → [Enviar] → NOT_SENT → [Marcar Enviado] → SENT
SENT → [Aceptar] | [Rechazar]
ACCEPTED → [Marcar Pagado] | [Pago Parcial]
Cualquier no-final → [Cancelar]
```

### Conversión
- Solo presupuestos ACCEPTED/SENT
- Botón "Convertir a Factura" / "Convertir a Albarán"

### PDF
- Botón "Descargar PDF" → fetch blob → download
- Preview en nueva pestaña

### Verificable
- Listar documentos con filtro tipo/estado/fecha
- Crear factura con 3 líneas → totales correctos
- Cambiar estado paso a paso hasta PAID
- Convertir presupuesto a factura
- Descargar PDF

---

## FASE 23: Inventario, Workers, Diary, Reminders

### Objetivo
Completar secciones restantes reutilizando patrones de Fase 21.

### Inventario (`src/pages/inventory.tsx`)
- Vista de productos centrada en stock
- 3 cards: Total Productos, Stock Bajo, Valor Total
- Tabla stock-focused + botón "Ajustar Stock"
- Filtro: Todos / En Stock / Stock Bajo / Sin Stock

### Workers (`src/pages/workers/index.tsx`, `[id].tsx`)
- CRUD tabla + filtro departamento
- Sub-recurso cursos en ficha del trabajador

### Diary (`src/pages/diary.tsx`)
- Lista de notas con pin toggle
- Filtro por fecha, editor título + contenido

### Reminders (`src/pages/reminders.tsx`)
- Lista con filtro prioridad y pendientes/completados
- Botón "Completar" rápido
- Badge color por prioridad
- Indicador "Vencido" si due_date < hoy

### APIs necesarias
- `src/api/workers.ts`, `diary.ts`, `reminders.ts`
- `src/hooks/use-workers.ts`, `use-diary.ts`, `use-reminders.ts`
- `src/types/worker.ts`, `diary.ts`, `reminder.ts`

---

## FASE 24: Reports, Export/Import, Audit, Admin, Settings

### Reports (`src/pages/reports.tsx`)
- Selector periodo: Mensual / Trimestral / Anual
- Cards resumen + gráfica barras (Recharts)
- APIs: `src/api/reports.ts`, `src/hooks/use-reports.ts`

### Export/Import
- Botones "Exportar CSV" en clientes, productos, proveedores
- Dialog importar: upload CSV + preview + confirmar
- API: `src/api/export-import.ts`

### Audit Log (`src/pages/audit.tsx` o dentro de admin)
- Tabla con filtros: acción, tipo entidad. Solo lectura.
- API: `src/api/audit.ts`

### Admin (`src/pages/admin.tsx`) - solo rol ADMIN
- System Info, Backup Info, Record counts
- API: `src/api/admin.ts`

### Settings (`src/pages/settings.tsx`)
- Theme toggle, Language selector, info versión, cerrar sesión

---

## FASE 25: PWA + Mobile + Deploy + Testing

### PWA
- `public/manifest.json` - App name, icons, theme_color
- Service Worker con Workbox (cache-first assets, network-first API)
- Icons 192x192 y 512x512

### Mobile
- Touch targets mínimo 44x44px
- Bottom nav ya existe (MobileNav)
- Pull-to-refresh en listas

### Backend: servir frontend estático
```python
# backend/app/main.py - añadir al final
app.mount("/assets", StaticFiles(directory="static/assets"))

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    file_path = os.path.join("static", full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse("static/index.html")
```

### Dockerfile multi-stage
```dockerfile
# Stage 1: Build frontend
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend + frontend static
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app/ ./app/
COPY --from=frontend-build /app/frontend/dist ./static
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
```

### CI/CD Frontend
- `.github/workflows/frontend-test.yml` - npm ci, lint, type-check, build

### Verificable
- `npm run build` → dist/ OK
- Docker multi-stage build funciona
- Deploy Railway sirve frontend + API
- PWA instalable
- Login → Dashboard → CRUD → Docs → PDF funcional

---

## Dependencias Instaladas (package.json)

Ya instaladas en node_modules:
- react, react-dom, react-router-dom
- @tanstack/react-query, axios, zustand
- react-hook-form, @hookform/resolvers, zod
- react-i18next, i18next
- recharts, sonner, lucide-react, date-fns
- clsx, tailwind-merge, class-variance-authority
- Radix UI primitives (dialog, dropdown-menu, select, label, etc.)
- tailwindcss, postcss, autoprefixer, vite, typescript

---

## Notas Importantes

- **No tocar el backend existente** excepto en Fase 25: main.py (static files), Dockerfile, CSP headers
- **Los 144 tests backend deben seguir pasando** siempre
- **Mobile-first CSS**: diseñar para móvil primero, expandir para desktop
- **Lazy loading**: todas las páginas con React.lazy()
- **Una fase a la vez**: completar, verificar build, commit, antes de pasar a la siguiente
