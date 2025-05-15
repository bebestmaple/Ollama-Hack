from datetime import datetime
from typing import List, Optional

from fastapi_pagination import Page, Params
from pydantic import BaseModel, field_validator, model_validator
from typing_extensions import Self

from src.ai_model.models import AIModelStatusEnum

from .models import EndpointStatusEnum


class EndpointCreate(BaseModel):
    url: str
    name: str = ""

    @field_validator("url")
    @classmethod
    def format_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            v = f"http://{v}"

        v = v.rstrip("/")

        return v

    @model_validator(mode="after")
    def set_name_if_none(self) -> Self:
        if not self.name:
            self.name = self.url
        return self


class EndpointBatchCreate(BaseModel):
    endpoints: List[EndpointCreate]


class EndpointInfo(BaseModel):
    id: int | None = None
    url: str
    name: str


class EndpointUpdate(BaseModel):
    name: str | None = None


class EndpointPerformanceInfo(BaseModel):
    id: int | None = None
    status: EndpointStatusEnum
    ollama_version: Optional[str] = None
    created_at: datetime


class EndpointWithPerformance(EndpointInfo):
    recent_performances: List[EndpointPerformanceInfo] = []


# New schemas for AI models associated with endpoints
class EndpointWithAIModelsRequest(Params):
    endpoint_id: int


class EndpointAIModelInfo(BaseModel):
    id: int
    name: str
    tag: str
    created_at: datetime
    status: AIModelStatusEnum
    token_per_second: Optional[float] = None
    max_connection_time: Optional[float] = None


class EndpointWithAIModels(EndpointWithPerformance):
    ai_models: Page[EndpointAIModelInfo]


class EndpointWithAIModelCount(EndpointWithPerformance):
    total_ai_model_count: int
    avaliable_ai_model_count: int
