from __future__ import annotations

from typing import Any, AnyStr, Dict, Optional, Tuple, Type, TYPE_CHECKING, TypeVar, Union

from pydantic import BaseModel
from quart.datastructures import FileStorage
from quart.typing import (
    HeadersValue as QuartHeadersValue,
    ResponseReturnValue as QuartResponseReturnValue,
    ResponseValue as QuartResponseValue,
    StatusCode,
)
from quart.wrappers import Response
from werkzeug.datastructures import Headers

if TYPE_CHECKING:
    from pydantic.dataclasses import Dataclass

try:
    from typing import Protocol
except ImportError:
    from typing_extensions import Protocol  # type: ignore


Model = Union[Type[BaseModel], Type["Dataclass"], Type]
PydanticModel = Union[Type[BaseModel], Type["Dataclass"]]

ResponseValue = Union[QuartResponseValue, PydanticModel]
HeadersValue = Union[QuartHeadersValue, PydanticModel]

ResponseReturnValue = Union[
    QuartResponseReturnValue,
    ResponseValue,
    Tuple[ResponseValue, HeadersValue],
    Tuple[ResponseValue, StatusCode],
    Tuple[ResponseValue, StatusCode, HeadersValue],
]


class WebsocketProtocol(Protocol):
    async def receive_json(self) -> dict:
        ...

    async def send_json(self, data: dict) -> None:
        ...


class TestClientProtocol(Protocol):
    async def _make_request(
        self,
        path: str,
        method: str,
        headers: Optional[Union[dict, Headers]],
        data: Optional[AnyStr],
        form: Optional[dict],
        files: Optional[Dict[str, FileStorage]],
        query_string: Optional[dict],
        json: Any,
        scheme: str,
        root_path: str,
        http_version: str,
        scope_base: Optional[dict],
    ) -> Response:
        ...


BM = TypeVar("BM", bound=BaseModel)
DC = TypeVar("DC", bound="Dataclass")
