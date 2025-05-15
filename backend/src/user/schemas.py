from typing import Optional

from pydantic import BaseModel


class UserAuth(BaseModel):
    username: str
    password: str


class UserInfo(BaseModel):
    id: int
    username: str
    is_admin: bool
    plan_id: Optional[int] = None


class UserUpdate(BaseModel):
    username: Optional[str] = None
    is_admin: Optional[bool] = None
    password: Optional[str] = None
    plan_id: Optional[int] = None


class Token(BaseModel):
    access_token: str
    token_type: str
