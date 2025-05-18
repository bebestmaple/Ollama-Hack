from fastapi import APIRouter, Depends

from src.user.service import get_current_admin_user

from .models import SystemSettingKey, SystemSettings
from .service import get_setting, get_settings, update_setting

setting_router = APIRouter(prefix="/setting", tags=["setting"])


@setting_router.get(
    "/",
    response_model=dict[SystemSettingKey, str],
    description="Get all settings",
    dependencies=[Depends(get_current_admin_user)],
)
async def _get_settings(
    settings: dict[SystemSettingKey, str] = Depends(get_settings),
) -> dict[SystemSettingKey, str]:
    return settings


@setting_router.get(
    "/{key}",
    response_model=SystemSettings,
    description="Get a setting by its key",
    dependencies=[Depends(get_current_admin_user)],
)
async def _get_setting(
    setting: SystemSettings = Depends(get_setting),
) -> SystemSettings:
    return setting


@setting_router.put(
    "/{key}",
    response_model=SystemSettings,
    description="Update a setting by its key",
    dependencies=[Depends(get_current_admin_user)],
)
async def _update_setting(
    setting: SystemSettings = Depends(update_setting),
) -> SystemSettings:
    return setting
