from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


# Endpoint相关模型
class EndpointBase(BaseModel):
    url: str
    name: Optional[str] = None


class EndpointCreate(EndpointBase):
    pass


class EndpointInDB(EndpointBase):
    id: int
    is_active: bool
    is_available: bool
    last_checked: datetime
    response_time: float

    class Config:
        orm_mode = True


class Endpoint(EndpointInDB):
    models: List["Model"] = []


class EndpointResponse(BaseModel):
    endpoints: List[Endpoint]
    count: int


# Model相关模型
class ModelBase(BaseModel):
    name: str
    display_name: Optional[str] = None


class ModelCreate(ModelBase):
    pass


class ModelInDB(ModelBase):
    id: int

    class Config:
        orm_mode = True


class Model(ModelInDB):
    endpoints: List[EndpointInDB] = []
    preferred_endpoint_id: Optional[int] = None


class ModelGetResponse(BaseModel):
    models: List[Model]
    count: int


# PerformanceTest相关模型
class PerformanceTestBase(BaseModel):
    endpoint_id: int
    model_id: int
    tokens_per_second: float
    response_time: float


class PerformanceTestCreate(PerformanceTestBase):
    pass


class PerformanceTestWithEndpoint(PerformanceTestBase):
    id: int
    timestamp: datetime
    endpoint: EndpointBase

    class Config:
        orm_mode = True


class PerformanceTestsResponse(BaseModel):
    performance_tests: List[PerformanceTestWithEndpoint]
    count: int


# ApiKey相关模型
class ApiKeyBase(BaseModel):
    name: str


class ApiKeyCreate(ApiKeyBase):
    pass


class ApiKey(ApiKeyBase):
    id: int
    key: str
    created_at: datetime
    is_active: bool

    class Config:
        orm_mode = True


# 批量导入端点
class EndpointBulkImport(BaseModel):
    endpoints: List[EndpointCreate]


# OpenAI兼容的请求和响应模型
class OllamaMessage(BaseModel):
    role: str
    content: str


class OllamaChatRequest(BaseModel):
    model: str
    messages: List[OllamaMessage]
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    max_tokens: Optional[int] = 2048
    stream: Optional[bool] = False


class OllamaChatResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[dict]
    usage: dict


# 用户相关模型
class UserBase(BaseModel):
    username: str
    is_admin: bool = False


class UserCreate(UserBase):
    password: str


class UserInDB(UserBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class User(UserInDB):
    pass


# 解决循环引用问题
Endpoint.update_forward_refs()
Model.update_forward_refs()
