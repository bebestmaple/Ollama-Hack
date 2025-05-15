from fastapi import APIRouter, Depends, status
from fastapi_pagination import Page

from src.user.service import get_current_admin_user

from .schemas import PlanResponse
from .service import create_plan, get_plan_by_id, get_plans, get_user_plan, update_plan

plan_router = APIRouter(prefix="/plan", tags=["plan"])


@plan_router.post(
    "/",
    response_model=PlanResponse,
    status_code=status.HTTP_201_CREATED,
    description="Create a new plan (admin only)",
    dependencies=[Depends(get_current_admin_user)],
)
async def _create_plan(
    plan: PlanResponse = Depends(create_plan),
) -> PlanResponse:
    """Create a new plan"""
    return plan


@plan_router.get(
    "/",
    response_model=Page[PlanResponse],
    description="List all plans (admin only)",
    dependencies=[Depends(get_current_admin_user)],
)
async def _get_plans(
    plans: Page[PlanResponse] = Depends(get_plans),
) -> Page[PlanResponse]:
    """List all plans"""
    return plans


@plan_router.get(
    "/me",
    response_model=PlanResponse,
    description="Get current user's plan",
)
async def _get_user_plan(
    plan: PlanResponse = Depends(get_user_plan),
) -> PlanResponse:
    """Get current user's plan"""
    return plan


@plan_router.get(
    "/{plan_id}",
    response_model=PlanResponse,
    description="Get a plan by ID (admin only)",
    dependencies=[Depends(get_current_admin_user)],
)
async def _get_plan(
    plan: PlanResponse = Depends(get_plan_by_id),
) -> PlanResponse:
    """Get a plan by ID"""
    return plan


@plan_router.patch(
    "/{plan_id}",
    response_model=PlanResponse,
    description="Update a plan (admin only)",
    dependencies=[Depends(get_current_admin_user)],
)
async def _update_plan(
    plan: PlanResponse = Depends(update_plan),
) -> PlanResponse:
    """Update a plan"""
    return plan
