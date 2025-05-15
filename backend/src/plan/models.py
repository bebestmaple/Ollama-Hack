import datetime
from typing import List, Optional

from sqlmodel import Field, Relationship

from src.core.utils import now
from src.database import SQLModel
from src.user.models import UserDB


class PlanDB(SQLModel, table=True):
    """
    Plan model for user subscription plans with rate limits
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: str = Field(default="")
    rpm: int = Field(default=60, description="Requests per minute limit")
    rpd: int = Field(default=10000, description="Requests per day limit")
    is_default: bool = Field(
        default=False, description="Whether this is the default plan for new users"
    )
    created_at: datetime.datetime = Field(default_factory=now)
    updated_at: datetime.datetime = Field(default_factory=now)

    # Relationships
    users: List["UserDB"] = Relationship(back_populates="plan")
