from dataclasses import dataclass
from typing import Optional

from attrs import define
from msgspec import Struct
from pydantic import BaseModel
from pydantic.dataclasses import dataclass as pydantic_dataclass


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
