# PLAN_FRONTEND.md - Frontend Web Dragofactu (Fases 19-25)

> **Última actualización:** 2026-02-08
> **Estado general:** Fases 19-25 completadas. Frontend web listo para deploy.

---

## Resumen de Estado

| Fase | Descripción | Estado | Fecha |
|------|-------------|--------|-------|
| 19 | Scaffolding + Auth + Routing | ✅ Completada | 2026-02-08 |
| 20 | Layout + Dashboard | ✅ Completada | 2026-02-08 |
| 21 | CRUD Clientes/Productos/Proveedores | ✅ Completada | 2026-02-08 |
| 22 | Documentos (line editor, status, PDF) | ✅ Completada | 2026-02-08 |
| 23 | Inventario, Workers, Diary, Reminders | ✅ Completada | 2026-02-08 |
| 24 | Reports, Export/Import, Audit, Admin, Settings | ✅ Completada | 2026-02-08 |
| **25** | **PWA + Mobile + Deploy + Testing** | **✅ Completada** | 2026-02-08 |

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

## FASE 22: Documentos ✅ COMPLETADA

### Archivos creados
- `src/types/document.ts` - Document, DocumentSummary, DocumentLine, DocumentCreate, etc.
- `src/api/documents.ts` - listDocuments, getDocument, createDocument, updateDocument, deleteDocument, changeStatus, convert, downloadPdf
- `src/lib/constants.ts` - DOC_TYPES, DOC_STATUSES, STATUS_TRANSITIONS, TAX_RATE, i18n maps
- `src/hooks/use-documents.ts` - useDocuments, useDocument, useCreateDocument, useUpdateDocument, useDeleteDocument, useChangeStatus, useConvertDocument
- `src/components/document-editor/status-badge.tsx` - Badge coloreado por estado
- `src/components/document-editor/totals-panel.tsx` - Subtotal/IVA(21%)/Total
- `src/components/document-editor/line-editor.tsx` - Editor de líneas con selector producto, cálculo automático, descuento %
- `src/pages/documents/index.tsx` - Lista con filtros tipo/estado, paginación
- `src/pages/documents/new.tsx` - Crear documento con line editor, selector cliente/fecha/tipo
- `src/pages/documents/detail.tsx` - Detalle + edición DRAFT + transiciones de estado + conversión + PDF download
- App.tsx: /documents, /documents/new, /documents/:id con lazy loading

---

## FASE 23: Inventario, Workers, Diary, Reminders ✅ COMPLETADA

### Archivos creados
- `src/types/worker.ts`, `diary.ts`, `reminder.ts` - Interfaces TypeScript
- `src/api/workers.ts`, `diary.ts`, `reminders.ts` - Funciones API completas
- `src/hooks/use-workers.ts`, `use-diary.ts`, `use-reminders.ts` - TanStack Query hooks
- `src/lib/validators.ts` - Añadidos: workerSchema, courseSchema, diarySchema, reminderSchema
- `src/pages/inventory.tsx` - Vista stock: 3 metric cards, filtro (All/In Stock/Low/No Stock), ajuste stock
- `src/pages/workers/index.tsx` - CRUD tabla + filtro departamento + detalle con cursos sub-recurso
- `src/pages/diary.tsx` - Lista con pin toggle, create/edit dialog con título + contenido + tags
- `src/pages/reminders.tsx` - Lista con filtro prioridad, pending/completed toggle, botón completar, overdue badge
- `src/i18n/es.json`, `en.json`, `de.json` - Claves añadidas para workers, diary, reminders CRUD
- App.tsx: /inventory, /workers, /diary, /reminders enrutan a páginas reales

---

## FASE 24: Reports, Export/Import, Audit, Admin, Settings ✅ COMPLETADA

### Archivos creados
- `src/types/report.ts`, `audit.ts`, `admin.ts` - Interfaces TypeScript
- `src/api/reports.ts`, `audit.ts`, `admin.ts`, `export-import.ts` - Funciones API
- `src/hooks/use-reports.ts`, `use-audit.ts`, `use-admin.ts` - TanStack Query hooks
- `src/pages/reports.tsx` - Selector periodo (mensual/trimestral/anual), 3-4 metric cards, Recharts bar chart
- `src/pages/audit.tsx` - Tabla read-only con filtros acción + tipo entidad, paginación
- `src/pages/admin.tsx` - System info (version, DB, record counts), Backup info (admin only)
- `src/pages/settings.tsx` - Theme toggle, language selector, info versión, user info, logout
- `src/i18n/*.json` - Claves añadidas: audit.*, export_import.*, admin.* expandido, nav.audit
- Sidebar + mobile-nav: añadido enlace /audit
- Clients/Products pages: botones Export CSV + Import CSV con dialog
- Suppliers page: botón Export CSV
- App.tsx: /reports, /audit, /admin, /settings enrutan a páginas reales

---

## FASE 25: PWA + Mobile + Deploy + Testing ✅ COMPLETADA

### Archivos creados/modificados
- `frontend/public/icon-192.png`, `icon-512.png` - PWA icons generados desde favicon.svg
- `frontend/index.html` - Añadidos meta tags PWA (apple-mobile-web-app-capable, apple-touch-icon)
- `frontend/vite.config.ts` - Integrado VitePWA plugin con manifest y Workbox runtime caching
- `backend/app/main.py` - Añadido SPA static file serving (StaticFiles + catch-all route), CSP actualizado para frontend
- `Dockerfile` - Movido a raíz, multi-stage: Node 20 (frontend build) + Python 3.11 (backend + static)
- `.github/workflows/frontend-test.yml` - CI: npm ci, tsc --noEmit, npm run build
- `vite-plugin-pwa` - Dependencia dev añadida, genera manifest.webmanifest y service worker automáticamente

### PWA
- Manifest generado por vite-plugin-pwa en build (dist/manifest.webmanifest)
- Service Worker con Workbox: precache 60 entries, runtime cache API con NetworkFirst (5min, 10s timeout)
- Icons: 192x192 y 512x512 PNG (+ maskable), apple-touch-icon

### Deploy
- Dockerfile multi-stage en raíz del repositorio (build context = repo root)
- Backend sirve frontend estático desde `static/` dir (solo si existe)
- CSP diferenciado: strict para API, permisivo para SPA (inline styles Tailwind)

### Verificado
- `npm run build` → dist/ OK (3.08s, 60 precached entries)
- `npx tsc --noEmit` → OK
- 144 backend tests passing

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
- vite-plugin-pwa (dev) - PWA manifest + Workbox service worker

---

## Notas Importantes

- **No tocar el backend existente** excepto en Fase 25: main.py (static files), Dockerfile, CSP headers
- **Los 144 tests backend deben seguir pasando** siempre
- **Mobile-first CSS**: diseñar para móvil primero, expandir para desktop
- **Lazy loading**: todas las páginas con React.lazy()
- **Una fase a la vez**: completar, verificar build, commit, antes de pasar a la siguiente
