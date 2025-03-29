from fastapi import APIRouter

from app.api.api_v1.endpoints import api_keys, auth, endpoints, models, ollama

api_router = APIRouter()
api_router.include_router(endpoints.router, prefix="/endpoints", tags=["endpoints"])
api_router.include_router(models.router, prefix="/models", tags=["models"])
api_router.include_router(api_keys.router, prefix="/api-keys", tags=["api-keys"])
api_router.include_router(ollama.router, prefix="/ollama", tags=["ollama"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
