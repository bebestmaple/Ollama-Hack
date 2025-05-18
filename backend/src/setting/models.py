import datetime
from enum import Enum
from typing import Self

from pydantic import model_validator
from sqlmodel import Field

from src.database import SQLModel
from src.utils import now


class SystemSettingKey(str, Enum):
    UPDATE_ENDPOINT_TASK_INTERVAL_HOURS = "update_endpoint_task_interval_hours"


class SystemSettings(SQLModel, table=True):
    key: SystemSettingKey = Field(primary_key=True)
    value: str
    created_at: datetime.datetime = Field(default_factory=now, nullable=False)

    def validate_value(self) -> None:
        if self.key == SystemSettingKey.UPDATE_ENDPOINT_TASK_INTERVAL_HOURS:
            int_value = int(self.value)
            if int_value < 1:
                raise ValueError("Value must be greater than 0")
            if int_value > 24 * 60:
                raise ValueError("Value must be less than 24 * 60")
            self.value = str(int_value)

    @model_validator(mode="after")
    def _validate_value(self) -> Self:
        self.validate_value()
        return self


DEFAULT_SETTINGS: dict[SystemSettingKey, str] = {
    SystemSettingKey.UPDATE_ENDPOINT_TASK_INTERVAL_HOURS: "24",
}
