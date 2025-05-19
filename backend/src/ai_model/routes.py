from fastapi import APIRouter, Depends
from fastapi_pagination import Page

from src.user.service import get_current_user

from .schemas import AIModelInfoWithEndpoint, AIModelInfoWithEndpointCount
from .service import get_ai_model_with_endpoints, get_ai_models_endpoint_counts

ai_model_router = APIRouter(
    prefix="/ai_model", tags=["ai_model"], dependencies=[Depends(get_current_user)]
)


@ai_model_router.get(
    "/",
    response_model=Page[AIModelInfoWithEndpointCount],
    description="Get all AI models with recent performance tests, with support for filtering, searching and sorting",
    response_description="List of AI models with their recent performance tests",
)
async def _get_ai_models(
    ai_model_pages: Page[AIModelInfoWithEndpointCount] = Depends(get_ai_models_endpoint_counts),
) -> Page[AIModelInfoWithEndpointCount]:
    return ai_model_pages


@ai_model_router.get(
    "/{ai_model_id}",
    response_model=AIModelInfoWithEndpoint,
    description="Get an AI model by ID",
    response_description="The AI model with its endpoints",
)
async def _get_ai_model_with_endpoints(
    ai_model_with_endpoints: AIModelInfoWithEndpoint = Depends(get_ai_model_with_endpoints),
) -> AIModelInfoWithEndpoint:
    return ai_model_with_endpoints
