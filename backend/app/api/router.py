"""
Main API router that includes all sub-routers.
"""
from fastapi import APIRouter
from app.api.v1 import auth

# Main API router
api_router = APIRouter()

# Include all routers
api_router.include_router(auth.router)

# Future routers will be added here:
# api_router.include_router(clients.router)
# api_router.include_router(products.router)
# api_router.include_router(documents.router)
# etc.
