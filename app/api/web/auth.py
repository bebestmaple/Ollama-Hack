from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from starlette.status import HTTP_303_SEE_OTHER

from app.api.api_v1.endpoints.auth import require_admin, require_auth
from app.api.web.utils import add_message, template_response
from app.crud import crud_user
from app.db.database import get_db
from app.schemas.schemas import UserCreate

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


# 用户管理页面 (仅管理员)
@router.get("/users", response_class=HTMLResponse)
async def user_management(
    request: Request, db: Session = Depends(get_db), _: None = Depends(require_admin)
):
    users = crud_user.get_users(db)
    current_username = request.session.get("user", "")

    return template_response(
        "users.html",
        {
            "request": request,
            "users": users,
            "current_username": current_username,
            "title": "用户管理",
        },
    )


# 创建用户 (仅管理员)
@router.post("/users/create")
async def create_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    is_admin: bool = Form(False),
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    try:
        existing_user = crud_user.get_user_by_username(db, username)
        if existing_user:
            add_message(request, f"用户名 '{username}' 已存在", "error")
            return RedirectResponse(url="/users", status_code=HTTP_303_SEE_OTHER)

        user_data = UserCreate(username=username, password=password, is_admin=is_admin)
        user = crud_user.create_user(db, user_data)
        add_message(request, f"成功创建用户: {user.username}", "success")
    except Exception as e:
        add_message(request, f"创建用户失败: {str(e)}", "error")

    return RedirectResponse(url="/users", status_code=HTTP_303_SEE_OTHER)


# 删除用户 (仅管理员)
@router.get("/users/{username}/delete")
async def delete_user(
    request: Request,
    username: str,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    try:
        current_username = request.session.get("user", "")
        if username == current_username:
            add_message(request, "不能删除当前登录用户", "error")
            return RedirectResponse(url="/users", status_code=HTTP_303_SEE_OTHER)

        user = crud_user.get_user_by_username(db, username)
        if not user:
            add_message(request, "用户不存在", "error")
            return RedirectResponse(url="/users", status_code=HTTP_303_SEE_OTHER)

        success = crud_user.delete_user(db, username)
        if success:
            add_message(request, f"已删除用户: {username}", "success")
        else:
            add_message(request, "删除用户失败", "error")
    except Exception as e:
        add_message(request, f"删除用户失败: {str(e)}", "error")

    return RedirectResponse(url="/users", status_code=HTTP_303_SEE_OTHER)


# 重置用户密码 (仅管理员)
@router.get("/users/{username}/reset-password")
async def reset_user_password(
    request: Request,
    username: str,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    try:
        new_password = crud_user.generate_password(12)
        success = crud_user.update_password(db, username, new_password)

        if success:
            add_message(
                request,
                f"已重置 {username} 的密码，新密码为: {new_password}",
                "success",
            )
        else:
            add_message(request, "重置密码失败，用户不存在", "error")
    except Exception as e:
        add_message(request, f"重置密码失败: {str(e)}", "error")

    return RedirectResponse(url="/users", status_code=HTTP_303_SEE_OTHER)


# 切换用户管理员状态 (仅管理员)
@router.get("/users/{username}/toggle-admin")
async def toggle_user_admin(
    request: Request,
    username: str,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    try:
        user = crud_user.get_user_by_username(db, username)
        if not user:
            add_message(request, "用户不存在", "error")
            return RedirectResponse(url="/users", status_code=HTTP_303_SEE_OTHER)

        # 切换管理员状态
        success = crud_user.toggle_admin(db, username)

        if success:
            new_status = "管理员" if not user.is_admin else "普通用户"
            add_message(request, f"已将 {username} 设置为{new_status}", "success")
        else:
            add_message(request, "更新用户状态失败", "error")
    except Exception as e:
        add_message(request, f"更新用户状态失败: {str(e)}", "error")

    return RedirectResponse(url="/users", status_code=HTTP_303_SEE_OTHER)
