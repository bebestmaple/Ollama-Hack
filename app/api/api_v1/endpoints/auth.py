from typing import List

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from starlette.status import HTTP_303_SEE_OTHER

from app.api.web.utils import add_message
from app.crud import crud_user
from app.db.database import get_db
from app.schemas.schemas import User, UserCreate, UserUpdate

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


# 管理员鉴权依赖
def require_admin(request: Request):
    if "user" not in request.session:
        raise HTTPException(
            status_code=HTTP_303_SEE_OTHER, headers={"Location": "/login"}
        )
    if not request.session.get("is_admin", False):
        raise HTTPException(status_code=403, detail="只有管理员可以访问此资源")
    return True


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


# 获取所有用户 (仅管理员)
@router.get("/users", response_model=List[User])
async def read_users(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin),
):
    users = crud_user.get_users(db, skip=skip, limit=limit)
    return users


# 获取单个用户 (仅管理员)
@router.get("/users/{username}", response_model=User)
async def read_user(
    request: Request,
    username: str,
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin),
):
    user = crud_user.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


# 创建用户 (仅管理员)
@router.post("/users", response_model=User)
async def create_user(
    request: Request,
    user: UserCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin),
):
    existing_user = crud_user.get_user_by_username(db, user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    return crud_user.create_user(db, user)


# 更新用户 (仅管理员)
@router.put("/users/{username}", response_model=User)
async def update_user(
    request: Request,
    username: str,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin),
):
    updated_user = crud_user.update_user(db, username, user_update)
    if not updated_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return updated_user


# 删除用户 (仅管理员)
@router.delete("/users/{username}")
async def delete_user(
    request: Request,
    username: str,
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin),
):
    # 不允许删除当前登录的用户
    current_user = request.session.get("user")
    if username == current_user:
        raise HTTPException(status_code=400, detail="不能删除当前登录用户")

    success = crud_user.delete_user(db, username)
    if not success:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"detail": "用户删除成功"}
