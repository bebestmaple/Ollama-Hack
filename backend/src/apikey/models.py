import datetime
from typing import List, Optional

from sqlmodel import Field, Relationship

from src.core.utils import now
from src.database import SQLModel
from src.user.models import UserDB


class ApiKeyDB(SQLModel, table=True):
    """API key model for authenticating API requests"""

    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(index=True, unique=True)
    name: str = Field(default="", index=True)
    created_at: datetime.datetime = Field(default_factory=now)
    last_used_at: Optional[datetime.datetime] = Field(default=None)
    revoked: bool = Field(default=False)

    # User relationship
    user_id: int = Field(foreign_key="user.id")
    user: UserDB = Relationship(back_populates="api_keys")

    # Usage logs relationship
    usage_logs: List["ApiKeyUsageLogDB"] = Relationship(back_populates="api_key")


class ApiKeyUsageLogDB(SQLModel, table=True):
    """API key usage log model for tracking API usage"""

    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime.datetime = Field(default_factory=now)
    endpoint: str = Field(index=True)
    method: str
    model: Optional[str] = Field(default=None)
    status_code: int

    # API key relationship
    api_key_id: int = Field(foreign_key="api_key.id")
    api_key: ApiKeyDB = Relationship(back_populates="usage_logs")
