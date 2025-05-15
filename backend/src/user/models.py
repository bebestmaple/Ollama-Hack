import datetime
from typing import List, Optional

from sqlmodel import Field, Relationship

from src.core.utils import now
from src.database import SQLModel


class UserDB(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    is_admin: bool = Field(default=False)
    username: str
    password: str
    created_at: datetime.datetime = Field(default_factory=now)

    # Add plan relationship
    plan_id: Optional[int] = Field(default=None, foreign_key="plan.id")
    plan: Optional["PlanDB"] = Relationship(back_populates="users")

    # Add API keys relationship
    api_keys: List["ApiKeyDB"] = Relationship(back_populates="user")


# Avoid circular import
from src.apikey.models import ApiKeyDB  # noqa: E402
from src.plan.models import PlanDB  # noqa: E402
