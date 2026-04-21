import sys
from dataclasses import dataclass
from typing import Annotated, Generic, TypeVar

from attrs import define
from msgspec import Struct
from pydantic import BaseModel, Field
from pydantic.dataclasses import dataclass as pydantic_dataclass

if sys.version_info >= (3, 12):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

try:
    from typing import NotRequired
except ImportError:
    from typing_extensions import NotRequired


@define
class ADetails:
    name: str
    age: int | None = None


class MDetails(Struct):
    name: str
    age: int | None = None


@dataclass
class DCDetails:
    name: str
    age: int | None = None


class PyDetails(BaseModel):
    name: str
    age: int | None = None


@pydantic_dataclass
class PyDCDetails:
    name: str
    age: int | None = None


class TDetails(TypedDict):
    name: str
    age: Annotated[int | None, Field(default=None)]


N = TypeVar("N")


class _TGDetails(TypedDict, Generic[N]):
    name: N
    age: NotRequired[int | None]


TGDetails = _TGDetails[str]
