from typing import Optional

from pydantic import BaseModel


class PlanBase(BaseModel):
    """Base Plan schema with common attributes"""

    name: str
    description: Optional[str] = ""
    rpm: int
    rpd: int
    is_default: Optional[bool] = False


class PlanCreate(PlanBase):
    """Schema for creating a new plan"""

    pass


class PlanUpdate(BaseModel):
    """Schema for updating an existing plan"""

    name: Optional[str] = None
    description: Optional[str] = None
    rpm: Optional[int] = None
    rpd: Optional[int] = None
    is_default: Optional[bool] = None


class PlanResponse(PlanBase):
    """Schema for plan response"""

    id: int

    class Config:
        from_attributes = True
