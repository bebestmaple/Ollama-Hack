from fastapi import APIRouter, Depends, status
from fastapi_pagination import Page

from .models import UserDB
from .schemas import Token, UserInfo
from .service import (
    change_current_user_password,
    create_user,
    get_current_admin_user,
    get_current_user,
    get_user_by_id,
    get_users,
    init_user,
    login_user,
    update_user,
)

user_router = APIRouter(prefix="/user", tags=["user"])


@user_router.post(
    "/init",
    status_code=status.HTTP_201_CREATED,
    description="Initialize the first user",
)
async def _init_user(result: None = Depends(init_user)) -> None:
    """
    Initialize the first user.
    """
    return result


@user_router.post(
    "/login",
    response_model=Token,
    description="Login a user",
    response_description="The logged in user",
)
async def _login(token: Token = Depends(login_user)) -> Token:
    return token


@user_router.get(
    "/me",
    response_model=UserInfo,
    description="Get the current user",
    response_description="The current user",
    dependencies=[Depends(get_current_user)],
)
async def _get_current_user(user: UserDB = Depends(get_current_user)) -> UserInfo:
    return UserInfo(**user.model_dump())


@user_router.patch(
    "/me/change-password",
    response_model=UserInfo,
    description="Change the current user's password",
    response_description="The updated user",
)
async def _change_password(
    user: UserDB = Depends(change_current_user_password),
) -> UserInfo:
    return UserInfo(**user.model_dump())


@user_router.post(
    "/",
    response_model=UserInfo,
    status_code=status.HTTP_201_CREATED,
    description="Create a new user",
    response_description="The created user",
    dependencies=[Depends(get_current_admin_user)],
)
async def _create_user(
    user: UserDB = Depends(create_user),
) -> UserInfo:
    return UserInfo(**user.model_dump())


@user_router.get(
    "/",
    response_model=Page[UserInfo],
    description="Get all users",
    response_description="The list of users",
    dependencies=[Depends(get_current_admin_user)],
)
async def _get_users(
    users: Page[UserInfo] = Depends(get_users),
) -> Page[UserInfo]:
    return users


@user_router.get(
    "/{user_id}",
    response_model=UserInfo,
    description="Get a user by id",
    response_description="The user info",
    dependencies=[Depends(get_current_admin_user)],
)
async def _get_user_by_id(
    user: UserDB = Depends(get_user_by_id),
) -> UserInfo:
    return UserInfo(**user.model_dump())


@user_router.patch(
    "/{user_id}",
    response_model=UserInfo,
    description="Update a user",
    response_description="The updated user",
    dependencies=[Depends(get_current_admin_user)],
)
async def _update_user(
    user: UserDB = Depends(update_user),
) -> UserInfo:
    """
    Update a user.
    """
    return UserInfo(**user.model_dump())
