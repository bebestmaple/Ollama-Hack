from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.api.web.utils import templates
from app.core.config import settings
from app.crud import crud_api_key, crud_endpoint, crud_model
from app.db.database import get_db

router = APIRouter()


# 首页
@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: Session = Depends(get_db)):
    endpoints, _ = crud_endpoint.get_endpoints(db)
    models = crud_model.get_available_models(db)
    api_keys = crud_api_key.get_api_keys(db)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "endpoints": endpoints,
            "models": models,
            "api_keys": api_keys,
            "title": settings.PROJECT_NAME,
        },
    )
