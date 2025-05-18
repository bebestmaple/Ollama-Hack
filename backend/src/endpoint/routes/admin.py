from fastapi import APIRouter, Depends, status

from src.endpoint.models import EndpointDB
from src.endpoint.schemas import (
    EndpointInfo,
)
from src.endpoint.service import (
    batch_create_or_update_endpoints,
    create_or_update_endpoint,
    delete_endpoint,
    update_endpoint,
)
from src.user.service import get_current_admin_user

endpoint_admin_router = APIRouter(tags=["endpoint"], dependencies=[Depends(get_current_admin_user)])


@endpoint_admin_router.post(
    "/",
    response_model=EndpointInfo,
    status_code=status.HTTP_201_CREATED,
    description="Create a new endpoint",
    response_description="The created endpoint",
)
async def _create_endpoint(
    endpoint: EndpointDB = Depends(create_or_update_endpoint),
) -> EndpointInfo:
    return EndpointInfo(**endpoint.model_dump())


@endpoint_admin_router.patch(
    "/{endpoint_id}",
    response_model=EndpointInfo,
    description="Update an endpoint",
    response_description="The updated endpoint",
    dependencies=[Depends(get_current_admin_user)],
)
async def _update_endpoint(
    endpoint: EndpointDB = Depends(update_endpoint),
) -> EndpointInfo:
    return EndpointInfo(**endpoint.model_dump())


@endpoint_admin_router.delete(
    "/{endpoint_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Delete an endpoint",
    dependencies=[Depends(get_current_admin_user)],
)
async def _delete_endpoint(
    endpoint_id: int,
    deleted: None = Depends(delete_endpoint),
) -> None:
    return None


@endpoint_admin_router.post(
    "/batch",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
    description="Batch create or update endpoints",
    response_description="The created or updated endpoints",
    dependencies=[Depends(get_current_admin_user)],
)
async def _batch_create_endpoints(
    endpoints: None = Depends(batch_create_or_update_endpoints),
) -> None:
    return None
