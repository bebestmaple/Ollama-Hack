from fastapi import Depends, HTTPException, status
from fastapi_pagination import Page, set_page
from fastapi_pagination.ext.sqlmodel import apaginate
from sqlalchemy import or_, true
from sqlmodel import and_, col, select, update

from src.core.dependencies import DBSessionDep
from src.logging import get_logger
from src.schema import SortOrder
from src.user.models import UserDB
from src.user.service import get_current_admin_user, get_current_user

from .models import PlanDB
from .schemas import PlanCreate, PlanFilterParams, PlanUpdate

logger = get_logger(__name__)


async def create_plan(
    session: DBSessionDep,
    plan_data: PlanCreate,
    current_user: UserDB = Depends(get_current_admin_user),
) -> PlanDB:
    """
    Create a new plan (admin only)
    """
    plan = PlanDB(**plan_data.model_dump())

    # If this plan is set as default, unset any existing default plan
    if plan.is_default:
        await session.execute(
            update(PlanDB).where(PlanDB.is_default == true()).values(is_default=False)  # type: ignore
        )

    session.add(plan)
    await session.commit()
    await session.refresh(plan)
    return plan


async def update_plan(
    session: DBSessionDep,
    plan_id: int,
    plan_data: PlanUpdate,
    current_user: UserDB = Depends(get_current_admin_user),
) -> PlanDB:
    """
    Update an existing plan (admin only)
    """
    plan = await get_plan_by_id(session, plan_id)

    # Update plan fields
    plan_updates = plan_data.model_dump(exclude_unset=True)
    for key, value in plan_updates.items():
        setattr(plan, key, value)

    # If this plan is being set as default, unset any existing default plan
    if plan_data.is_default:
        await session.execute(
            update(PlanDB)
            .where(and_(PlanDB.id != plan_id, PlanDB.is_default == true()))
            .values(is_default=False)
        )

    await session.commit()
    await session.refresh(plan)
    return plan


async def get_plan_by_id(session: DBSessionDep, plan_id: int) -> PlanDB:
    """
    Get a plan by its ID
    """
    plan = await session.get(PlanDB, plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan with ID {plan_id} not found",
        )
    return plan


async def get_plans(
    session: DBSessionDep,
    params: PlanFilterParams = Depends(),
) -> Page[PlanDB]:
    """
    Get all plans with support for filtering, searching and sorting (admin only)
    """
    set_page(Page[PlanDB])
    query = select(PlanDB)

    # 添加搜索条件
    if params.search:
        search_term = f"%{params.search}%"
        query = query.where(
            or_(col(PlanDB.name).ilike(search_term), col(PlanDB.description).ilike(search_term))
        )

    # 添加排序
    if params.order_by:
        order_column = getattr(PlanDB, params.order_by.value)
        if params.order == SortOrder.DESC:
            order_column = order_column.desc()
        query = query.order_by(order_column)

    return await apaginate(session, query, params)


async def get_default_plan(session: DBSessionDep) -> PlanDB:
    """
    Get the default plan for new users
    """
    result = await session.execute(select(PlanDB).where(PlanDB.is_default == true()))
    default_plan = result.scalars().first()

    if not default_plan:
        # If no default plan exists, create one
        default_plan = PlanDB(
            name="Free",
            description="Default free plan with basic limits",
            rpm=10,
            rpd=1000,
            is_default=True,
        )
        session.add(default_plan)
        await session.commit()
        await session.refresh(default_plan)

    return default_plan


async def get_user_plan(session: DBSessionDep, user: UserDB = Depends(get_current_user)) -> PlanDB:
    """
    Get the plan for a specific user
    """
    if user.plan_id:
        plan = await get_plan_by_id(session, user.plan_id)
        return plan
    else:
        # If user has no plan, assign the default plan
        default_plan = await get_default_plan(session)
        user.plan_id = default_plan.id
        await session.commit()
        return default_plan


async def delete_plan(session: DBSessionDep, plan_id: int) -> None:
    """
    Delete a plan (admin only)
    """
    plan = await get_plan_by_id(session, plan_id)
    await session.delete(plan)
    await session.commit()
