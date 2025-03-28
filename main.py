from contextlib import asynccontextmanager

import uvicorn
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.api.api_v1.api import api_router
from app.api.web.router import web_router
from app.core.config import settings
from app.db.database import Base, engine
from app.services.endpoint_service import check_all_endpoints

# 创建数据库表
Base.metadata.create_all(bind=engine)


# 创建和启动定时任务
@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = BackgroundScheduler()
    # 每5分钟检查一次所有端点的可用性
    scheduler.add_job(check_all_endpoints, "interval", hours=5)
    scheduler.start()
    yield


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

# 添加会话中间件
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 添加API路由
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(web_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
