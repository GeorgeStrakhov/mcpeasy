"""
Admin API interface for React frontend
"""
from fastapi import APIRouter

from .api import router as api_router

# Create main admin router - only API routes now (React frontend handles UI)
admin_router = APIRouter()

# Include API routes
admin_router.include_router(api_router, prefix="/api")

__all__ = ["admin_router"]