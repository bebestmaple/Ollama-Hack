from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, Relationship

from src.ai_model.models import AIModelDB, EndpointAIModelDB
from src.core.utils import now
from src.database import SQLModel


class EndpointStatusEnum(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    FAKE = "fake"


class EndpointDB(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str
    name: str
    created_at: datetime = Field(default_factory=now)

    ai_models: list["AIModelDB"] = Relationship(
        back_populates="endpoints",
        link_model=EndpointAIModelDB,
    )
    performances: list["EndpointPerformanceDB"] = Relationship(
        back_populates="endpoint",
        sa_relationship_kwargs={"order_by": "EndpointPerformanceDB.created_at.desc()"},
    )

    ai_model_links: list["EndpointAIModelDB"] = Relationship(
        back_populates="endpoint",
    )


class EndpointPerformanceDB(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    status: EndpointStatusEnum = Field(default=EndpointStatusEnum.UNAVAILABLE)
    ollama_version: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=now)

    endpoint_id: Optional[int] = Field(foreign_key="endpoint.id", default=None)

    endpoint: EndpointDB = Relationship(back_populates="performances")
