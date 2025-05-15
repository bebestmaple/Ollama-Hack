from datetime import datetime
from typing import Optional

from fastapi_pagination import Page, Params
from pydantic import BaseModel

from .models import AIModelStatusEnum


class AIModelWithEndpointRequest(Params):
    ai_model_id: int


# AI模型相关的Schema
class AIModelInfo(BaseModel):
    id: int | None = None
    name: str
    tag: str
    created_at: datetime


class AIModelInfoWithEndpointCount(AIModelInfo):
    total_endpoint_count: int
    avaliable_endpoint_count: int


class AIModelPerformance(BaseModel):
    id: int
    status: AIModelStatusEnum
    token_per_second: Optional[float] = None
    connection_time: Optional[float] = None
    total_time: Optional[float] = None
    created_at: datetime


class ModelFromEndpointInfo(BaseModel):
    id: int
    url: str
    name: str
    created_at: datetime

    status: AIModelStatusEnum
    token_per_second: Optional[float] = None
    max_connection_time: Optional[float] = None

    model_performances: list[AIModelPerformance]


class AIModelInfoWithEndpoint(AIModelInfo):
    endpoints: Page[ModelFromEndpointInfo]
