"""
Admin Authentication Middleware
"""
from typing import Optional
from fastapi import Header, HTTPException
from app.config.settings import settings


async def admin_auth(x_admin_key: Optional[str] = Header(default=None)):
    """Verify admin API key from header"""
    if not settings.admin_api_key:
        raise HTTPException(status_code=503, detail="Admin API is not configured")
    if not x_admin_key or x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True


