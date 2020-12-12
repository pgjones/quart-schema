from __future__ import annotations

from typing import Any, Type, TypeVar

from pydantic import BaseModel

try:
    from typing import Protocol
except ImportError:
    from typing_extensions import Protocol  # type: ignore


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
