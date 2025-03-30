import secrets
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Ollama 中转平台"
    API_V1_STR: str = "/api/v1"
    LOG_LEVEL: str = "DEBUG"

    # 数据库配置
    DATABASE_URL: str = "sqlite:///./data/data.db"

    # 安全配置
    SECRET_KEY: str = secrets.token_urlsafe(32)

    # CORS配置
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    class Config:
        case_sensitive = True


settings = Settings()
