from fastapi import APIRouter

from app.api.web import (
    api_key,
    endpoint,
    index,
    model,
)

web_router = APIRouter(include_in_schema=False)

# 注册各模块路由
web_router.include_router(index.router)
web_router.include_router(endpoint.router)
web_router.include_router(model.router)
web_router.include_router(api_key.router)
