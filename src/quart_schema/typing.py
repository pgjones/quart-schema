from __future__ import annotations

from typing import Any, Type, TypeVar

from pydantic import BaseModel

try:
    from typing import Protocol, TypedDict
except ImportError:
    from typing_extensions import Protocol, TypedDict  # type: ignore


class Dataclass(Protocol):
    __pydantic_model__: Type[BaseModel]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        ...


class WebsocketProtocol(Protocol):
    async def receive_json(self) -> dict:
        ...

    async def send_json(self, data: dict) -> None:
        ...


BM = TypeVar("BM", bound=BaseModel)
DC = TypeVar("DC", bound=Dataclass)


class ExternalDocumentationObject(TypedDict, total=False):
    description: str
    url: str


class TagObject(TypedDict, total=False):
    name: str
    description: str
    externalDocs: ExternalDocumentationObject  # noqa: N815
