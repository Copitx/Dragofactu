<div align="center">

# 🐉 Dragofactu

**Professional ERP for construction & service companies — built to replace Excel forever.**

[![Backend](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)](backend)
[![Frontend](https://img.shields.io/badge/Frontend-React%20%2B%20TypeScript-61DAFB?logo=react&logoColor=222)](frontend)
[![Desktop](https://img.shields.io/badge/Desktop-PySide6-41CD52?logo=qt&logoColor=white)](dragofactu)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-4169E1?logo=postgresql&logoColor=white)](backend)
[![Deploy](https://img.shields.io/badge/Deploy-Railway-0B0D0E?logo=railway&logoColor=white)](railway.toml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

*Multi-tenant SaaS ERP · Multi-platform (web, desktop, API) · Production-ready*

</div>

---

## 🏗️ What is Dragofactu?

Dragofactu is a full-featured ERP system built specifically for **construction, trade, and service companies** that are tired of managing their business with spreadsheets. It handles the complete document lifecycle — quotes → delivery notes → invoices — plus projects, expenses, inventory, workers, and more.

Originally built to replace a 9-year-old Excel workflow managing **700+ delivery notes/year, 120+ active projects, and 2,500+ historical records**.

---

## ✨ Key Features

### 📄 Documents & Invoicing
- Full document lifecycle: **Quotes → Delivery Notes → Invoices**
- Status workflow: `Draft → Sent → Accepted → Paid` with one-click transitions
- **PDF generation** with company branding, trade name, execution location, client reference, payment method, and page numbers
- Batch invoicing: **group multiple delivery notes into a single invoice** in one click
- Quick mark-as-paid with payment date tracking
- Send documents directly by **email with custom SMTP per company** and personalizable templates

### 🏗️ Projects / Job Sites
- Full project management module: create job sites linked to clients
- Track **expenses by category** (materials, labor, subcontract, other)
- Link any document (quote, delivery note, invoice) to a project
- **Real-time KPIs per project**: budget vs. expenses vs. invoiced → margin %
- Create a document from a project and it auto-fills client + job site location

### 🏬 Smart Client Defaults
- Configure **payment terms, default discount, and payment method** per client
- When you select a client on a new document, due date and payment method fill **automatically**
- Default discount auto-applies to every line when a product is selected

### 📦 Supplier Catalog
- Maintain a **purchase price catalog per supplier** with supplier references
- Search across all catalogs from the **line editor** — see purchase price and margin % before adding to a document
- Global catalog search with margin comparison across suppliers

### 📊 Dashboard & Alerts
- Construction-specific KPIs: active projects, uninvoiced delivery notes, overdue invoices (+30d), due soon (15d)
- **Sidebar badge** on Documents showing how many invoices need attention — visible without entering the page
- Recent pending documents list with direct navigation

### 🔍 Global Search
- **Cmd+K / Ctrl+K** search palette — finds clients, documents, and projects simultaneously
- Debounced, parallel queries, results are instantly navigable

### 📁 Import / Export
- Export clients, products, suppliers to **CSV**
- Import wizard with **3-step preview**: select file → preview rows → confirm import
- Supports **CSV and XLSX** formats
- Preview shows valid/error/skipped counts before any data is written

### 🏢 Multi-tenant & Multi-user
- Complete **company isolation** — every query scoped by `company_id`
- Role-based access: `Admin`, `Management`, `Warehouse`, `Read-only`
- Admins can **create and manage users within their company**
- Per-company **SMTP email configuration**

### 🛡️ Superadmin Panel
- Platform-level admin dashboard: view all companies, all users, global audit log
- Manage users across companies: edit roles, reset passwords, deactivate
- Company drill-down: stats, user list, inline management via slide-over panel
- Superadmin status **only settable via server script** — never via API

### 📱 PWA & Mobile
- Web app installable as a **Progressive Web App** on any device
- Responsive design — works on phones, tablets, and desktops
- Mobile navigation with bottom nav bar

### 🌍 Internationalization
- Full **Spanish, English, and German** support across web and desktop
- Language switcher without page reload

---

## 🏛️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Clients                              │
│  🌐 Web App (React + TS + PWA)                              │
│  🖥️  Desktop App (Python + PySide6)                         │
│  🤖 Any REST client                                         │
└─────────────────┬───────────────────────────────────────────┘
                  │ HTTPS / JWT
┌─────────────────▼───────────────────────────────────────────┐
│                  FastAPI Backend (Railway)                   │
│  Multi-tenant · RBAC · Audit log · Rate limiting            │
│  bcrypt + JWT · HttpOnly refresh cookies                    │
│  Redis (distributed blacklist + rate limits)                │
└─────────────────┬───────────────────────────────────────────┘
                  │
        ┌─────────▼──────────┐
        │   PostgreSQL (prod) │   SQLite (dev)
        └────────────────────┘
```

---

## 🛠️ Tech Stack

### Backend
| Technology | Version | Purpose |
|---|---|---|
| ![Python](https://img.shields.io/badge/-Python-3776AB?logo=python&logoColor=white) | 3.11+ | Core language |
| ![FastAPI](https://img.shields.io/badge/-FastAPI-009688?logo=fastapi&logoColor=white) | 0.115+ | REST API framework |
| ![SQLAlchemy](https://img.shields.io/badge/-SQLAlchemy-D71F00) | 2.x | ORM |
| ![PostgreSQL](https://img.shields.io/badge/-PostgreSQL-4169E1?logo=postgresql&logoColor=white) | 15+ | Production database |
| ![Redis](https://img.shields.io/badge/-Redis-DC382D?logo=redis&logoColor=white) | optional | Token blacklist + rate limiting |
| ![ReportLab](https://img.shields.io/badge/-ReportLab-CC0000) | 4.x | PDF generation |

### Frontend
| Technology | Version | Purpose |
|---|---|---|
| ![React](https://img.shields.io/badge/-React-61DAFB?logo=react&logoColor=222) | 18 | UI framework |
| ![TypeScript](https://img.shields.io/badge/-TypeScript-3178C6?logo=typescript&logoColor=white) | 5.x | Type safety |
| ![Vite](https://img.shields.io/badge/-Vite-646CFF?logo=vite&logoColor=white) | 5.x | Build tool |
| ![TailwindCSS](https://img.shields.io/badge/-Tailwind-06B6D4?logo=tailwindcss&logoColor=white) | 3.x | Styling |
| ![TanStack Query](https://img.shields.io/badge/-TanStack%20Query-FF4154) | 5.x | Server state & caching |
| ![Zustand](https://img.shields.io/badge/-Zustand-5A67D8) | 5.x | Client state |
| shadcn/ui | — | Accessible component library |

### Desktop
| Technology | Purpose |
|---|---|
| Python + PySide6 | Native Qt6 desktop app |
| Hybrid mode | Local SQLite or connected to remote API |
| Offline queue | Operations queued locally when offline, synced on reconnect |

---

## 🚀 Quick Start

### Backend (local dev)

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend (local dev)

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
npm run build        # production build
npx tsc --noEmit    # type check
```

### Desktop

```bash
./start_dragofactu.sh
```

> Admin credentials are bootstrapped via `DEFAULT_ADMIN_PASSWORD` environment variable or a secure one-time password generated on first run.

---

## 🧪 Testing

```bash
# Backend — 169+ tests
cd backend && python -m pytest tests/ -v

# Frontend — type check + build
cd frontend && npx tsc --noEmit && npm run build
```

---

## 🔐 Security Highlights

- 🔒 **HttpOnly cookies** for refresh tokens — no localStorage exposure
- 🛡️ **CORS hardened** — wildcard disabled in production, explicit `ALLOWED_ORIGINS` required
- 🔑 **bcrypt** password hashing (12 rounds) + strict password policy
- 📋 **Audit log** on every write operation — full traceability
- 🚦 **Rate limiting** with optional Redis backend (in-memory fallback for dev)
- 🏷️ **RBAC** with 4 roles and granular permission matrix
- 📧 **Password reset** via email with SHA-256 tokens, 60-min TTL, single-use
- 🔧 **Superadmin** promotion only via server-side script — never via API
- 📵 **API docs** disabled in production by default (`ENABLE_API_DOCS=true` to enable)
- 🐳 **Docker secrets** via environment variables — no hardcoded defaults

---

## 🚢 Production Deployment (Railway)

The app ships as a **single Docker container**: Node.js builds the frontend, Python serves it alongside the API via FastAPI's static file serving.

```dockerfile
# Multi-stage: Node 20 (build frontend) → Python 3.11 (serve everything)
CMD ["python", "startup.py"]   # applies schema migrations + execs uvicorn
```

Required environment variables:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | JWT signing key (32+ chars) |
| `ALLOWED_ORIGINS` | Comma-separated allowed CORS origins |
| `REDIS_URL` | Optional: enables distributed rate limiting |
| `METRICS_TOKEN` | Protects the `/metrics` endpoint |
| `APP_URL` | Base URL for password reset email links |

---

## 📁 Repository Structure

```
backend/                   FastAPI API, models, schemas, tests
  app/
    api/v1/                REST endpoints (one file per domain)
    models/                SQLAlchemy models
    core/                  PDF generation, security, email
  startup.py               Schema migration script (runs on deploy)
  tests/                   169+ pytest tests

frontend/                  React + TypeScript web client
  src/
    api/                   Axios clients per entity
    components/            shadcn/ui + layout + document editor
    hooks/                 TanStack Query hooks
    pages/                 Lazy-loaded page components
    stores/                Zustand (auth, ui)
    i18n/                  es.json · en.json · de.json

dragofactu/                Modular PySide6 desktop client
  services/api_client.py   HTTP client with offline cache
  ui/                      Qt6 widget modules

scripts/
  create_superadmin_noninteractive.py   Bootstrap superadmin on production DB
  security/                             Audit & credential rotation scripts
```

---

## 📜 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

---

<div align="center">

Built with ❤️ for the construction industry · Dragofactu v3.3.0

</div>
