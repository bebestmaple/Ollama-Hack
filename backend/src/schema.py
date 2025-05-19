from enum import StrEnum
from typing import Generic, Optional, TypeVar

from fastapi_pagination import Params


class SortOrder(StrEnum):
    ASC = "asc"
    DESC = "desc"


T = TypeVar("T", bound=StrEnum)


class FilterParams(Params, Generic[T]):
    search: Optional[str] = None
    order_by: Optional[T] = None
    order: Optional[SortOrder] = SortOrder.DESC
