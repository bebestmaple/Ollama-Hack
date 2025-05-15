import datetime
import uuid
from typing import List, Optional, Tuple

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import false, func
from sqlalchemy.orm import selectinload
from sqlmodel import select

from src.core.dependencies import DBSessionDep
from src.core.utils import now
from src.logging import get_logger
from src.plan.models import PlanDB
from src.plan.service import get_user_plan
from src.user.models import UserDB
from src.user.service import get_current_user, get_user_by_id

from .models import ApiKeyDB, ApiKeyUsageLogDB
from .schemas import ApiKeyCreate, ApiKeyUsageStats

logger = get_logger(__name__)


def generate_api_key() -> str:
    """Generate a new random API key"""
    return str(uuid.uuid4())


async def create_api_key(
    session: DBSessionDep,
    api_key_data: ApiKeyCreate,
    user: UserDB = Depends(get_current_user),
) -> ApiKeyDB:
    """Create a new API key for the current user"""
    # Create the API key
    api_key = ApiKeyDB(
        key=generate_api_key(),
        name=api_key_data.name,
        user_id=user.id or 0,  # Ensure non-null value
    )

    # Save to database
    session.add(api_key)
    await session.commit()
    await session.refresh(api_key)

    return api_key


async def get_api_keys_for_user(
    session: DBSessionDep,
    user: UserDB = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
) -> List[ApiKeyDB]:
    """Get all API keys for the current user"""
    result = await session.execute(
        select(ApiKeyDB)
        .where(ApiKeyDB.user_id == user.id, ApiKeyDB.revoked == false())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_api_key_by_id(
    session: DBSessionDep,
    api_key_id: int,
    user: UserDB = Depends(get_current_user),
) -> ApiKeyDB:
    """Get an API key by ID"""
    result = await session.execute(
        select(ApiKeyDB)
        .where(ApiKeyDB.id == api_key_id, ApiKeyDB.user_id == user.id)
        .options(selectinload(ApiKeyDB.user).selectinload(UserDB.plan))  # type: ignore
    )
    api_key = result.scalars().first()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    return api_key


async def delete_api_key(
    session: DBSessionDep,
    api_key_id: int,
    user: UserDB = Depends(get_current_user),
) -> None:
    """Delete (revoke) an API key"""
    api_key = await get_api_key_by_id(session, api_key_id, user)

    # Mark as revoked instead of deleting
    api_key.revoked = True

    await session.commit()


async def get_api_key_by_key(
    session: DBSessionDep,
    key: str,
) -> ApiKeyDB:
    """Get an API key by the actual key value"""
    result = await session.execute(
        select(ApiKeyDB).where(ApiKeyDB.key == key, ApiKeyDB.revoked == false())
    )
    api_key = result.scalars().first()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return api_key


async def validate_api_key(
    session: DBSessionDep,
    key: str,
) -> Tuple[ApiKeyDB, UserDB, PlanDB]:
    """Validate an API key and return the key, user and plan"""
    api_key = await get_api_key_by_key(session, key)

    # Update last used time
    api_key.last_used_at = now()

    # Get user separately to avoid async/greenlet issues
    user = await get_user_by_id(session, api_key.user_id)

    # Get plan
    plan = await get_user_plan(session, user)
    await session.commit()

    return api_key, user, plan


async def log_api_key_usage(
    session: DBSessionDep,
    api_key: ApiKeyDB,
    endpoint: str,
    method: str,
    model: Optional[str],
    status_code: int,
) -> Optional[ApiKeyUsageLogDB]:
    """Log API key usage"""
    # Ensure api_key.id is not None
    if api_key.id is None:
        logger.warning("Attempted to log usage for API key with null ID")
        return None

    # Create usage log
    usage_log = ApiKeyUsageLogDB(
        api_key_id=api_key.id,
        endpoint=endpoint,
        method=method,
        model=model,
        status_code=status_code,
    )

    # Save to database
    session.add(usage_log)
    await session.commit()
    await session.refresh(usage_log)

    return usage_log


async def get_api_key_from_request(
    request: Request,
    session: DBSessionDep,
) -> Tuple[ApiKeyDB, UserDB, PlanDB]:
    """Extract and validate API key from request"""
    # Get API key from header or query param
    api_key = request.headers.get("X-API-Key")

    if not api_key:
        # Try to get from query param
        api_key = request.query_params.get("api_key")

    if not api_key:
        # Try to get from Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            api_key = auth_header.replace("Bearer ", "")

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key missing",
        )

    return await validate_api_key(session, api_key)


async def check_rate_limits(
    session: DBSessionDep,
    api_key: ApiKeyDB,
    plan: PlanDB,
) -> None:
    """Check if the API key has exceeded rate limits"""
    await session.refresh(api_key)
    await session.refresh(plan)
    _now = now()

    # Check RPM (requests per minute)
    one_minute_ago = _now - datetime.timedelta(minutes=1)
    rpm_result = await session.execute(
        select(func.count())
        .select_from(ApiKeyUsageLogDB)
        .where(
            ApiKeyUsageLogDB.api_key_id == api_key.id,
            ApiKeyUsageLogDB.timestamp >= one_minute_ago,
        )
    )
    rpm_count = rpm_result.scalar_one()

    if rpm_count >= plan.rpm:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {rpm_count}/{plan.rpm} requests per minute",
        )

    # Check RPD (requests per day)
    today_start = datetime.datetime(_now.year, _now.month, _now.day)
    rpd_result = await session.execute(
        select(func.count())
        .select_from(ApiKeyUsageLogDB)
        .where(
            ApiKeyUsageLogDB.api_key_id == api_key.id,
            ApiKeyUsageLogDB.timestamp >= today_start,
        )
    )
    rpd_count = rpd_result.scalar_one()

    if rpd_count >= plan.rpd:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {rpd_count}/{plan.rpd} requests per day",
        )


async def get_api_key_usage_stats(
    session: DBSessionDep,
    api_key_id: int,
    user: UserDB = Depends(get_current_user),
) -> ApiKeyUsageStats:
    """Get usage statistics for an API key"""
    # Verify ownership of the API key
    api_key = await get_api_key_by_id(session, api_key_id, user)

    _now = now()
    today_start = datetime.datetime(_now.year, _now.month, _now.day)
    thirty_days_ago = _now - datetime.timedelta(days=30)

    # Total requests
    total_result = await session.execute(
        select(func.count())
        .select_from(ApiKeyUsageLogDB)
        .where(ApiKeyUsageLogDB.api_key_id == api_key.id)
    )
    total_requests = total_result.scalar_one()

    # Last 30 days requests
    month_result = await session.execute(
        select(func.count())
        .select_from(ApiKeyUsageLogDB)
        .where(
            ApiKeyUsageLogDB.api_key_id == api_key.id,
            ApiKeyUsageLogDB.timestamp >= thirty_days_ago,
        )
    )
    last_30_days_requests = month_result.scalar_one()

    # Today's requests
    today_result = await session.execute(
        select(func.count())
        .select_from(ApiKeyUsageLogDB)
        .where(
            ApiKeyUsageLogDB.api_key_id == api_key.id,
            ApiKeyUsageLogDB.timestamp >= today_start,
        )
    )
    requests_today = today_result.scalar_one()

    # Successful requests (status code < 400)
    success_result = await session.execute(
        select(func.count())
        .select_from(ApiKeyUsageLogDB)
        .where(
            ApiKeyUsageLogDB.api_key_id == api_key.id,
            ApiKeyUsageLogDB.status_code < 400,
        )
    )
    successful_requests = success_result.scalar_one()

    # Failed requests (status code >= 400)
    failed_result = await session.execute(
        select(func.count())
        .select_from(ApiKeyUsageLogDB)
        .where(
            ApiKeyUsageLogDB.api_key_id == api_key.id,
            ApiKeyUsageLogDB.status_code >= 400,
        )
    )
    failed_requests = failed_result.scalar_one()

    # Requests per day in the last 30 days
    daily_stats = []
    for i in range(30):
        day = _now - datetime.timedelta(days=i)
        day_start = datetime.datetime(day.year, day.month, day.day)
        day_end = day_start + datetime.timedelta(days=1)

        day_result = await session.execute(
            select(func.count())
            .select_from(ApiKeyUsageLogDB)
            .where(
                ApiKeyUsageLogDB.api_key_id == api_key.id,
                ApiKeyUsageLogDB.timestamp >= day_start,
                ApiKeyUsageLogDB.timestamp < day_end,
            )
        )
        count = day_result.scalar_one()

        daily_stats.append({"date": day_start.strftime("%Y-%m-%d"), "count": count})

    return ApiKeyUsageStats(
        total_requests=total_requests,
        last_30_days_requests=last_30_days_requests,
        requests_today=requests_today,
        successful_requests=successful_requests,
        failed_requests=failed_requests,
        requests_per_day=daily_stats,
    )
