# DRAGOFACTU

ERP multi-plataforma para gestion empresarial con 3 clientes activos:
- Desktop (Python + PySide6)
- Web (React + TypeScript)
- API REST (FastAPI + PostgreSQL)

## Estado del proyecto

- Backend en produccion (Railway): activo
- Frontend web v3.0.0: completo
- Desktop: funcional en modo hibrido (local/remoto)
- Fase 26 (correo por empresa): implementada base + plantillas personalizables
- Endurecimiento de seguridad: aplicado por sprints y reforzado operativamente

## Arquitectura

```text
Desktop (PySide6) ──┐
Web (React+TS) ─────┼──> FastAPI (multi-tenant, JWT, RBAC) ──> PostgreSQL (Railway)
                    │
                    └──> Redis (rate limit y blacklist distribuidos)
```

## Funcionalidades principales

- Facturacion completa (presupuestos, albaranes, facturas)
- Workflow de estados de documentos
- CRUD de clientes, productos, proveedores
- Inventario y ajustes de stock
- Trabajadores, diario y recordatorios
- Informes, auditoria y export/import CSV
- Multi-idioma (es/en/de)
- Modo offline en desktop (cache + cola de operaciones)
- PWA en frontend web

## Seguridad y operaciones (resumen)

- CORS endurecido en no-debug
- OpenAPI/Docs controlables por entorno
- `/metrics` protegido por token
- Refresh token web en cookie HttpOnly
- Compose sin secretos por defecto
- Soporte Redis para controles distribuidos
- Runbooks y scripts operativos para cierre de seguridad

## Stack tecnologico

### Backend
- FastAPI
- SQLAlchemy 2
- PostgreSQL
- Pydantic v2
- JWT + bcrypt
- pytest

### Frontend
- React 18
- TypeScript
- Vite 5
- TailwindCSS
- shadcn/ui
- TanStack Query
- Zustand

### Desktop
- Python 3.10+
- PySide6
- ReportLab

## Inicio rapido

### Backend local

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend local

```bash
cd frontend
npm install
npm run dev
```

### Desktop

```bash
./start_dragofactu.sh
```

Nota sobre credenciales:
- No hay credencial fija hardcodeada como politica.
- El bootstrap admin se define por entorno (`DEFAULT_ADMIN_PASSWORD`) o se genera temporalmente de forma segura.

## Calidad y testing

Backend:

```bash
cd backend
python -m pytest tests/ -v
```

Frontend:

```bash
cd frontend
npm run type-check
npm run build
npm run test:e2e
```

## Despliegue (Railway)

Variables de entorno clave (produccion):
- `DATABASE_URL`
- `SECRET_KEY`
- `ALLOWED_ORIGINS`
- `METRICS_TOKEN`
- `REDIS_URL`

## Estructura principal

```text
backend/                API FastAPI + tests
frontend/               Cliente web React
dragofactu/             Cliente desktop modular
scripts/security/       Scripts de cierre y verificacion de seguridad
docs/                   Documentacion tecnica y operativa
```

## Higiene de repositorio

- Rama principal activa: `main`
- Remoto: `origin` (GitHub)
- Hay ramas historicas remotas (`feature/multi-tenant-api`, `stable`) para evaluar limpieza cuando se quiera.
- No se detectan artefactos sensibles/temporales trackeados (`.env`, `.pyc`, `.DS_Store`, DB local).

## Documentacion recomendada

- `AGENTS.md`
- `CLAUDE.md`
- `MEMORIA_LARGO_PLAZO.md`
- `PLAN_FRONTEND.md`
- `PLAN_BACKEND.md`
- `PLAN_DESKTOP_PYTHON.md`
- `PLAN_OPERACIONES_SEGURIDAD.md`

## Licencia

MIT
