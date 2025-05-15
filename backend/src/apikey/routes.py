from typing import List

from fastapi import APIRouter, Depends, status

from .schemas import (
    ApiKeyInfo,
    ApiKeyResponse,
    ApiKeyUsageStats,
)
from .service import (
    create_api_key,
    delete_api_key,
    get_api_key_by_id,
    get_api_key_usage_stats,
    get_api_keys_for_user,
)

apikey_router = APIRouter(prefix="/apikey", tags=["apikey"])


@apikey_router.post(
    "/",
    response_model=ApiKeyResponse,
    status_code=status.HTTP_201_CREATED,
    description="Create a new API key",
)
async def _create_api_key(
    api_key: ApiKeyResponse = Depends(create_api_key),
) -> ApiKeyResponse:
    """Create a new API key"""
    return api_key


@apikey_router.get(
    "/",
    response_model=List[ApiKeyInfo],
    description="List all API keys for the current user",
)
async def _get_api_keys(
    api_keys: List[ApiKeyInfo] = Depends(get_api_keys_for_user),
) -> List[ApiKeyInfo]:
    """List all API keys for the current user"""
    return api_keys


@apikey_router.get(
    "/{api_key_id}",
    response_model=ApiKeyInfo,
    description="Get API key details",
)
async def _get_api_key(
    api_key: ApiKeyInfo = Depends(get_api_key_by_id),
) -> ApiKeyInfo:
    """Get API key details"""
    return api_key


@apikey_router.delete(
    "/{api_key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Delete (revoke) an API key",
)
async def _delete_api_key(
    api_key_result: None = Depends(delete_api_key),
) -> None:
    """Delete (revoke) an API key"""
    return None


@apikey_router.get(
    "/{api_key_id}/stats",
    response_model=ApiKeyUsageStats,
    description="Get usage statistics for an API key",
)
async def _get_api_key_stats(
    stats: ApiKeyUsageStats = Depends(get_api_key_usage_stats),
) -> ApiKeyUsageStats:
    """Get usage statistics for an API key"""
    return stats
