from pydantic import BaseModel, Field


class Pagination(BaseModel):
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=10, ge=0, le=100)
