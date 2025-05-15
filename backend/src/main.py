from contextlib import asynccontextmanager

import bcrypt
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import Env, get_config
from .database import create_db_and_tables, sessionmanager
from .logging import get_logger
from .routes import router

bcrypt.__about__ = bcrypt  # type: ignore


config = get_config()
logger = get_logger(__name__)

logger.debug(f"Config: {config}")

# no doc other than dev env
docs_url = "/docs" if config.app.env == Env.DEV else None


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield
    if sessionmanager._engine is not None:
        await sessionmanager.close()


app = FastAPI(
    lifespan=lifespan,
    docs_url=docs_url,
    redoc_url=None,
    title="Ollama Hack Backend",
    description="Ollama Hack Backend",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
