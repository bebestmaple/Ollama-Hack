import datetime
import re
from datetime import timezone
from functools import partial


def now() -> datetime.datetime:
    """
    Return current UTC time.
    """
    return datetime.datetime.now(timezone.utc)


_snake_1 = partial(re.compile(r"(.)((?<![^A-Za-z])[A-Z][a-z]+)").sub, r"\1_\2")
_snake_2 = partial(re.compile(r"([a-z0-9])([A-Z])").sub, r"\1_\2")


def snake_case(string: str) -> str:
    """
    Convert the class name of a SQLModel class to a table name.
    """
    return _snake_2(_snake_1(string.rstrip("DB"))).casefold()
