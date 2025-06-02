from fastapi import APIRouter, Depends
from fastapi_pagination import Page

from src.endpoint.schemas import (
    EndpointWithAIModelCount,
    EndpointWithAIModels,
)
from src.endpoint.service import (
    get_endpoint_with_ai_models,
    get_endpoints_with_ai_model_counts,
)
from src.user.service import get_current_user

endpoint_user_router = APIRouter(tags=["endpoint"], dependencies=[Depends(get_current_user)])


@endpoint_user_router.get(
    "/",
    response_model=Page[EndpointWithAIModelCount],
    description="Get all endpoints with recent performance tests and AI model counts, with support for filtering, searching and sorting",
    response_description="List of endpoints with their recent performance tests and AI model counts",
)
async def _get_endpoints(
    endpoint_pages: Page[EndpointWithAIModelCount] = Depends(get_endpoints_with_ai_model_counts),
) -> Page[EndpointWithAIModelCount]:
    return endpoint_pages


@endpoint_user_router.get(
    "/{endpoint_id:int}",
    response_model=EndpointWithAIModels,
    description="Get an endpoint by ID with recent performance tests and associated AI models",
    response_description="The endpoint with recent performance tests and paginated AI models",
)
async def _get_endpoint_by_id(
    endpoint_with_ai_models: EndpointWithAIModels = Depends(get_endpoint_with_ai_models),
) -> EndpointWithAIModels:
    return endpoint_with_ai_models
