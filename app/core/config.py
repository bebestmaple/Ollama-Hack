import secrets
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Ollama中转平台"
    API_V1_STR: str = "/api/v1"

    # 数据库配置
    DATABASE_URL: str = "sqlite:///./data/data.db"

    # 安全配置
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # CORS配置
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # 根目录
    ROOT_DIR: Path = Path(__file__).resolve().parent.parent.parent

    # Ollama API端点测试相关参数
    ENDPOINT_TEST_TIMEOUT: int = 10  # 测试端点超时时间（秒）
    ENDPOINT_TEST_MODEL: str = "llama2"  # 用于测试的默认模型

    class Config:
        case_sensitive = True


settings = Settings()
