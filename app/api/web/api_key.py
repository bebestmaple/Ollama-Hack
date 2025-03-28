from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from starlette.status import HTTP_303_SEE_OTHER

from app.api.web.utils import add_message, templates
from app.crud import crud_api_key
from app.db.database import get_db
from app.schemas.schemas import ApiKeyCreate

router = APIRouter()


# API密钥管理页面
@router.get("/api-keys", response_class=HTMLResponse)
async def api_key_management(request: Request, db: Session = Depends(get_db)):
    api_keys = crud_api_key.get_api_keys(db)

    return templates.TemplateResponse(
        "api_keys.html",
        {"request": request, "api_keys": api_keys, "title": "API密钥管理"},
    )


# 创建API密钥
@router.post("/api-keys/create")
async def create_api_key(
    request: Request, name: str = Form(...), db: Session = Depends(get_db)
):
    try:
        api_key_data = ApiKeyCreate(name=name)
        db_api_key = crud_api_key.create_api_key(db, api_key_data)

        add_message(
            request,
            f"成功创建API密钥: {db_api_key.name} (密钥: {db_api_key.key})",
            "success",
        )
    except Exception as e:
        add_message(request, f"创建API密钥失败: {str(e)}", "error")

    return RedirectResponse(url="/api-keys", status_code=HTTP_303_SEE_OTHER)


# 停用API密钥
@router.get("/api-keys/{api_key_id}/deactivate")
async def deactivate_api_key(
    request: Request, api_key_id: int, db: Session = Depends(get_db)
):
    try:
        db_api_key = crud_api_key.deactivate_api_key(db, api_key_id)

        if db_api_key:
            add_message(request, f"成功停用API密钥: {db_api_key.name}", "success")
        else:
            add_message(request, "API密钥不存在", "error")
    except Exception as e:
        add_message(request, f"停用API密钥失败: {str(e)}", "error")

    return RedirectResponse(url="/api-keys", status_code=HTTP_303_SEE_OTHER)


# 删除API密钥
@router.get("/api-keys/{api_key_id}/delete")
async def delete_api_key(
    request: Request, api_key_id: int, db: Session = Depends(get_db)
):
    try:
        db_api_key = crud_api_key.get_api_key_by_id(db, api_key_id)
        if not db_api_key:
            add_message(request, "API密钥不存在", "error")
            return RedirectResponse(url="/api-keys", status_code=HTTP_303_SEE_OTHER)

        api_key_name = db_api_key.name
        success = crud_api_key.delete_api_key(db, api_key_id)

        if success:
            add_message(request, f"成功删除API密钥: {api_key_name}", "success")
        else:
            add_message(request, "删除API密钥失败", "error")
    except Exception as e:
        add_message(request, f"删除API密钥失败: {str(e)}", "error")

    return RedirectResponse(url="/api-keys", status_code=HTTP_303_SEE_OTHER)
