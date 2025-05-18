from fastapi import APIRouter, Depends, status
from fastapi_pagination import Page

from src.endpoint.models import EndpointDB, EndpointTestTask
from src.endpoint.schemas import EndpointInfo, TaskInfo, TaskWithEndpoint
from src.endpoint.service import (
    batch_create_or_update_endpoints,
    create_or_update_endpoint,
    delete_endpoint,
    get_task_by_id,
    get_tasks,
    manual_trigger_endpoint_test,
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


@endpoint_admin_router.post(
    "/{endpoint_id}/test",
    response_model=TaskInfo,
    status_code=status.HTTP_202_ACCEPTED,
    description="Manually trigger a test for an endpoint",
    response_description="The created test task",
)
async def _trigger_endpoint_test(
    task: EndpointTestTask = Depends(manual_trigger_endpoint_test),
) -> TaskInfo:
    return TaskInfo(**task.model_dump())


@endpoint_admin_router.get(
    "/tasks",
    response_model=Page[TaskInfo],
    description="Get all tasks with filtering and sorting",
    response_description="List of tasks",
)
async def _get_tasks(
    tasks: Page[TaskInfo] = Depends(get_tasks),
) -> Page[TaskInfo]:
    return tasks


@endpoint_admin_router.get(
    "/tasks/{task_id}",
    response_model=TaskWithEndpoint,
    description="Get a task by ID with its endpoint",
    response_description="The task with its endpoint",
)
async def _get_task_by_id(
    task: TaskWithEndpoint = Depends(get_task_by_id),
) -> TaskWithEndpoint:
    return task
