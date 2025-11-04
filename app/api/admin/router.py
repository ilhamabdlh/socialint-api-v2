"""
Admin Write API Router
Aggregates all admin write routes.
"""
from fastapi import APIRouter

from app.api.admin.brand_write import router as brand_write_router
from app.api.admin.campaign_write import router as campaign_write_router

router = APIRouter()

router.include_router(brand_write_router, tags=["admin-write-brand"])
router.include_router(campaign_write_router, tags=["admin-write-campaign"])


