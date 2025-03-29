from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from starlette.status import HTTP_303_SEE_OTHER

from app.api.web.utils import add_message
from app.crud import crud_user
from app.db.database import get_db

router = APIRouter()


# 登录接口
@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = crud_user.authenticate_user(db, username, password)
    if user:
        request.session["user"] = username
        request.session["is_admin"] = user.is_admin
        add_message(request, "登录成功", "success")
        return RedirectResponse(url="/", status_code=HTTP_303_SEE_OTHER)
    add_message(request, "用户名或密码错误", "error")
    return RedirectResponse(url="/login", status_code=HTTP_303_SEE_OTHER)


# 鉴权依赖
def require_auth(request: Request):
    if "user" not in request.session:
        raise HTTPException(
            status_code=HTTP_303_SEE_OTHER, headers={"Location": "/login"}
        )


# 修改密码接口
@router.post("/change-password")
async def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
):
    if "user" not in request.session:
        add_message(request, "请先登录", "error")
        return RedirectResponse(url="/login", status_code=HTTP_303_SEE_OTHER)

    if new_password != confirm_password:
        add_message(request, "新密码与确认密码不匹配", "error")
        return RedirectResponse(url="/change-password", status_code=HTTP_303_SEE_OTHER)

    username = request.session["user"]
    user = crud_user.authenticate_user(db, username, current_password)

    if not user:
        add_message(request, "当前密码不正确", "error")
        return RedirectResponse(url="/change-password", status_code=HTTP_303_SEE_OTHER)

    success = crud_user.update_password(db, username, new_password)

    if success:
        add_message(request, "密码修改成功", "success")
        return RedirectResponse(url="/", status_code=HTTP_303_SEE_OTHER)
    else:
        add_message(request, "密码修改失败", "error")
        return RedirectResponse(url="/change-password", status_code=HTTP_303_SEE_OTHER)
