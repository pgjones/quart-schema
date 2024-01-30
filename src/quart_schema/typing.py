from __future__ import annotations

from typing import Any, AnyStr, Callable, Dict, List, Optional, Tuple, Type, TYPE_CHECKING, Union

from quart import Quart
from quart.datastructures import FileStorage
from quart.typing import (
    HeadersValue as QuartHeadersValue,
    ResponseReturnValue as QuartResponseReturnValue,
    ResponseValue as QuartResponseValue,
    StatusCode,
)
from quart.wrappers import Response
from werkzeug.datastructures import Headers

try:
    from typing import Protocol
except ImportError:
    from typing_extensions import Protocol  # type: ignore

if TYPE_CHECKING:
    from attrs import AttrsInstance
    from msgspec import Struct
    from pydantic import BaseModel
    from pydantic.dataclasses import Dataclass


class DataclassProtocol(Protocol):
    __dataclass_fields__: Dict
    __dataclass_params__: Dict
    __post_init__: Optional[Callable]


ModelTypes = Union["AttrsInstance", "BaseModel", "Dataclass", "DataclassProtocol", "Struct"]
Model = Union[ModelTypes, List[ModelTypes], Dict[str, ModelTypes]]
ResponseValue = Union[QuartResponseValue, Type[Model]]
HeadersValue = Union[QuartHeadersValue, Model]

ResponseReturnValue = Union[
    QuartResponseReturnValue,
    ResponseValue,
    Tuple[ResponseValue, HeadersValue],
    Tuple[ResponseValue, StatusCode],
    Tuple[ResponseValue, StatusCode, HeadersValue],
]


class WebsocketProtocol(Protocol):
    async def receive_json(self) -> dict: ...

    async def send_json(self, data: dict) -> None: ...


class TestClientProtocol(Protocol):
    app: Quart

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
    ) -> Response: ...
