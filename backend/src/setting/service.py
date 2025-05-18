from fastapi import HTTPException, status
from sqlmodel import select

from src.database import DBSessionDep

from .models import DEFAULT_SETTINGS, SystemSettingKey, SystemSettings


async def init_settings(session: DBSessionDep) -> None:
    """
    Initialize the settings.
    """
    for key, value in DEFAULT_SETTINGS.items():
        try:
            await get_setting(session, key)
        except HTTPException as e:
            if e.status_code == status.HTTP_404_NOT_FOUND:
                await create_setting(session, key, value)
            else:
                raise e


async def create_setting(
    session: DBSessionDep, key: SystemSettingKey, value: str
) -> SystemSettings:
    """
    Create a setting.
    """
    setting = SystemSettings(key=key, value=value)
    session.add(setting)
    await session.commit()
    await session.refresh(setting)
    return setting


async def get_setting(session: DBSessionDep, key: SystemSettingKey) -> SystemSettings:
    """
    Get a setting by its key.
    """
    query = select(SystemSettings).where(SystemSettings.key == key)
    result = await session.execute(query)
    setting = result.scalar_one_or_none()
    if not setting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting not found")
    return setting  # type: ignore


async def update_setting(
    session: DBSessionDep, key: SystemSettingKey, value: str
) -> SystemSettings:
    """
    Update a setting by its key.
    """
    setting = await get_setting(session, key)
    setting.value = value
    try:
        setting.validate_value()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    session.add(setting)
    await session.commit()
    await session.refresh(setting)
    if key == SystemSettingKey.UPDATE_ENDPOINT_TASK_INTERVAL_HOURS:
        from src.endpoint.scheduler import get_scheduler

        scheduler = get_scheduler()
        await scheduler.schedule_periodic_endpoint_updates()
    return setting


async def get_settings(session: DBSessionDep) -> dict[SystemSettingKey, str]:
    """
    Get all settings.
    """
    query = select(SystemSettings)
    result = await session.execute(query)
    return {setting.key: setting.value for setting in result.scalars().all()}
