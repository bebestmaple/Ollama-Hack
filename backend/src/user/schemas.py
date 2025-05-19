from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, Field

from src.schema import FilterParams


class UserSortField(StrEnum):
    ID = "id"
    USERNAME = "username"
    IS_ADMIN = "is_admin"
    PLAN_ID = "plan_id"


class UserFilterParams(FilterParams[UserSortField]):
    pass


class UserAuth(BaseModel):
    username: str
    password: str = Field(min_length=8, max_length=128)


class UserInfo(BaseModel):
    id: int
    username: str
    is_admin: bool
    plan_id: Optional[int] = None
    plan_name: Optional[str] = None


class UserUpdate(BaseModel):
    username: Optional[str] = None
    is_admin: Optional[bool] = None
    password: Optional[str] = None
    plan_id: Optional[int] = None


class Token(BaseModel):
    access_token: str
    token_type: str
