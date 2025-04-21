import sys
from dataclasses import dataclass
from typing import Annotated, Optional

from attrs import define
from msgspec import Struct
from pydantic import BaseModel, Field
from pydantic.dataclasses import dataclass as pydantic_dataclass

if sys.version_info >= (3, 12):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict


@define
class ADetails:
    name: str
    age: Optional[int] = None


class MDetails(Struct):
    name: str
    age: Optional[int] = None


@dataclass
class DCDetails:
    name: str
    age: Optional[int] = None


class PyDetails(BaseModel):
    name: str
    age: Optional[int] = None


@pydantic_dataclass
class PyDCDetails:
    name: str
    age: Optional[int] = None


class TDetails(TypedDict):
    name: str
    age: Annotated[Optional[int], Field(default=None)]
