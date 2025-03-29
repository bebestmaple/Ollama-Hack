from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER

from app.api.api_v1.endpoints.auth import require_auth
from app.api.web.utils import add_message, template_response

router = APIRouter()


# 登录页面
@router.get("/login")
async def login_page(request: Request):
    return template_response("login.html", {"request": request})


# 注销接口
@router.get("/logout")
async def logout(request: Request, _: None = Depends(require_auth)):
    request.session.clear()
    add_message(request, "已注销", "info")
    return RedirectResponse(url="/login", status_code=HTTP_303_SEE_OTHER)


# 修改密码页面
@router.get("/change-password")
async def change_password_page(request: Request, _: None = Depends(require_auth)):
    username = request.session.get("user", "")
    return template_response(
        "change_password.html",
        {"request": request, "title": "修改密码", "username": username},
    )
