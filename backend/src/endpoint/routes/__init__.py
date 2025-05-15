from fastapi import APIRouter

from .admin import endpoint_admin_router
from .user import endpoint_user_router

endpoint_router = APIRouter(prefix="/endpoint")
endpoint_router.include_router(endpoint_user_router)
endpoint_router.include_router(endpoint_admin_router)

__all__ = ["endpoint_router"]
