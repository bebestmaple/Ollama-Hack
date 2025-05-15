from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi_pagination import Page, Params, set_page
from fastapi_pagination.ext.sqlmodel import apaginate
from sqlalchemy import func
from sqlmodel import select

from src.config import get_config
from src.core.dependencies import DBSessionDep
from src.logging import get_logger

from .models import UserDB
from .schemas import Token, UserAuth, UserInfo, UserUpdate
from .utils import create_access_token, hash_password, verify_password

logger = get_logger(__name__)
config = get_config()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v2/user/login")


async def get_users(session: DBSessionDep, params: Params = Depends()) -> Page[UserInfo]:
    """
    Get all users.
    """
    set_page(Page[UserInfo])
    result: Page[UserDB] = await apaginate(session, select(UserDB), params)
    return Page(
        items=[UserInfo(**user.model_dump()) for user in result.items],
        page=result.page,
        size=result.size,
        total=result.total,
    )


async def get_user_by_id(session: DBSessionDep, user_id: int) -> UserDB:
    """
    Validate a user id.
    """
    user = await session.get(UserDB, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


async def get_user_by_username(session: DBSessionDep, username: str) -> UserDB:
    """
    Validate a user username.
    """
    result = await session.execute(select(UserDB).where(UserDB.username == username))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


async def create_user(session: DBSessionDep, user_auth: UserAuth) -> UserDB:
    """
    Create a new user.
    """
    from src.plan.service import get_default_plan

    user_model = UserDB(**user_auth.model_dump())
    user_model.password = hash_password(user_model.password)
    result = await session.execute(select(UserDB).where(UserDB.username == user_model.username))
    if result.first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")

    # Assign default plan
    default_plan = await get_default_plan(session)
    user_model.plan_id = default_plan.id

    session.add(user_model)
    await session.commit()
    await session.refresh(user_model)
    if user_model.id == 1:
        user_model.is_admin = True
        await session.commit()
        await session.refresh(user_model)
    return user_model


async def update_user(session: DBSessionDep, user_id: int, fields: UserUpdate) -> UserDB:
    """
    Update a user.
    """
    user = await get_user_by_id(session, user_id)
    for key, value in fields.model_dump(exclude_none=True).items():
        if key == "plan_id" and not value:
            # Don't set plan_id to None
            continue
        setattr(user, key, value)
    if fields.password:
        user.password = hash_password(fields.password)
    await session.commit()
    await session.refresh(user)
    return user


async def login_user(
    session: DBSessionDep,
    user_auth: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """
    Login a user.
    """
    UnauthorizedException = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
    )
    try:
        user = await get_user_by_username(session, user_auth.username)
        user_data = {
            "id": user.id,
        }
    except HTTPException as e:
        raise UnauthorizedException from e
    if not verify_password(user_auth.password, user.password):
        raise UnauthorizedException
    return Token(access_token=create_access_token(user_data), token_type="Bearer")


async def get_current_user(
    session: DBSessionDep,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> UserDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, config.app.secret_key, algorithms=[config.app.algorithm])
        user_id = payload.get("id")
        if user_id is None:
            raise credentials_exception
        user = await get_user_by_id(session, user_id)
        return user
    except jwt.InvalidTokenError as e:
        raise credentials_exception from e


async def get_current_admin_user(
    current_user: Annotated[UserDB, Depends(get_current_user)],
) -> UserDB:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return current_user


async def get_user_count(session: DBSessionDep) -> int:
    """
    Get the total number of users.
    """
    result = await session.execute(select(func.count()).select_from(UserDB))
    count = result.scalar_one()
    return count


async def change_current_user_password(
    session: DBSessionDep,
    old_password: str,
    new_password: str,
    user: UserDB = Depends(get_current_user),
) -> UserDB:
    """
    Change a user's password.
    """
    if not verify_password(old_password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid old password")
    user.password = hash_password(new_password)
    await session.commit()
    await session.refresh(user)
    return user


async def init_user(session: DBSessionDep, request: UserAuth) -> None:
    """
    Initialize the first user.
    """

    if await get_user_count(session) > 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")
    await create_user(session, request)
