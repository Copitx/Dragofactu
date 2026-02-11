"""
Main API router that includes all sub-routers.
"""
from fastapi import APIRouter
from app.api.v1 import auth, clients, products, suppliers, workers, diary, reminders, documents, dashboard, export_import, audit, reports, admin, company

# Main API router
api_router = APIRouter()

# Auth (public endpoints)
api_router.include_router(auth.router)

# CRUD routers (all protected)
api_router.include_router(clients.router)
api_router.include_router(products.router)
api_router.include_router(suppliers.router)
api_router.include_router(workers.router)
api_router.include_router(diary.router)
api_router.include_router(reminders.router)

# Documents router (Fase 5)
api_router.include_router(documents.router)

# Dashboard stats (Fase 10)
api_router.include_router(dashboard.router)

# Fase 16 features
api_router.include_router(export_import.router)
api_router.include_router(audit.router)
api_router.include_router(reports.router)

# Company settings
api_router.include_router(company.router)

# Fase 18 - Admin & monitoring
api_router.include_router(admin.router)
