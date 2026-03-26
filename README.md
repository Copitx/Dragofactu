# Dragofactu

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Backend](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)](backend)
[![Frontend](https://img.shields.io/badge/Frontend-React%20%2B%20TypeScript-61DAFB?logo=react&logoColor=222)](frontend)
[![Desktop](https://img.shields.io/badge/Desktop-PySide6-41CD52?logo=qt&logoColor=white)](dragofactu)
[![Database](https://img.shields.io/badge/Database-PostgreSQL-4169E1?logo=postgresql&logoColor=white)](backend)
[![Deploy](https://img.shields.io/badge/Deploy-Railway-0B0D0E?logo=railway&logoColor=white)](railway.toml)
[![Security](https://img.shields.io/badge/Security-Hardened-0A7D34)](docs)

Multi-platform ERP with three active clients:

- Desktop app (Python + PySide6)
- Web app (React + TypeScript)
- REST API (FastAPI + PostgreSQL)

## Project Snapshot

- Production backend on Railway: active
- Web frontend v3.0.0: completed
- Desktop app: stable hybrid mode (local/remote)
- Phase 26 (per-company email): base implementation shipped with customizable templates
- Security hardening: completed in sprints and reinforced with operational runbooks

## Architecture

```text
Desktop (PySide6) ──┐
Web (React + TS) ───┼──> FastAPI (multi-tenant, JWT, RBAC) ──> PostgreSQL (Railway)
                    │
                    └──> Redis (distributed rate-limit + token blacklist)
```

## Feature Highlights

- Full invoicing flow (quotes, delivery notes, invoices)
- Document lifecycle workflow (draft to paid)
- CRUD for clients, products, and suppliers
- Inventory and stock adjustment workflows
- Workers, diary, and reminders modules
- Reports, audit log, CSV export/import
- Multi-language support (Spanish, English, German)
- Desktop offline mode (cache + operation queue)
- PWA support on the web client

## Tech Stack

### Backend

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.x-D71F00?logo=sqlalchemy&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063)
![Pytest](https://img.shields.io/badge/Pytest-Tested-0A9EDC?logo=pytest&logoColor=white)

### Frontend

![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=222)
![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?logo=typescript&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-5.x-646CFF?logo=vite&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-3.x-06B6D4?logo=tailwindcss&logoColor=white)
![Zustand](https://img.shields.io/badge/Zustand-State%20Store-5A67D8)
![TanStack Query](https://img.shields.io/badge/TanStack%20Query-Data%20Fetching-FF4154)

### Desktop

![Python](https://img.shields.io/badge/Python-Desktop-3776AB?logo=python&logoColor=white)
![Qt](https://img.shields.io/badge/Qt-PySide6-41CD52?logo=qt&logoColor=white)
![ReportLab](https://img.shields.io/badge/PDF-ReportLab-CC0000)

## Security and Operations

- Hardened CORS behavior for non-debug environments
- API docs exposure controlled by environment flags
- `/metrics` endpoint protected with token-based access
- Web refresh tokens stored in HttpOnly cookies
- Docker Compose without insecure default secrets
- Optional Redis backend for distributed security controls
- Security closure runbooks and verification scripts included

## Quick Start

### 1) Backend (local)

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2) Frontend (local)

```bash
cd frontend
npm install
npm run dev
```

### 3) Desktop

```bash
./start_dragofactu.sh
```

Admin bootstrap credentials are never hardcoded. Use `DEFAULT_ADMIN_PASSWORD` or a securely generated temporary password.

## Testing and Quality

### Backend tests

```bash
cd backend
python -m pytest tests/ -v
```

### Frontend checks

```bash
cd frontend
npm run type-check
npm run build
npm run test:e2e
```

## Deployment (Railway)

Key production environment variables:

- `DATABASE_URL`
- `SECRET_KEY`
- `ALLOWED_ORIGINS`
- `METRICS_TOKEN`
- `REDIS_URL`

## Repository Layout

```text
backend/                FastAPI API + tests
frontend/               React web client
dragofactu/             Modular desktop client
scripts/security/       Security validation and closure scripts
docs/                   Technical and operational documentation
```

## Important Docs

- [AGENTS.md](AGENTS.md)
- [CLAUDE.md](CLAUDE.md)
- [MEMORIA_LARGO_PLAZO.md](MEMORIA_LARGO_PLAZO.md)
- [PLAN_FRONTEND.md](PLAN_FRONTEND.md)
- [PLAN_BACKEND.md](PLAN_BACKEND.md)
- [PLAN_DESKTOP_PYTHON.md](PLAN_DESKTOP_PYTHON.md)
- [PLAN_OPERACIONES_SEGURIDAD.md](PLAN_OPERACIONES_SEGURIDAD.md)

## License

This project is licensed under the MIT License.
