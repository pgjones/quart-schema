from __future__ import annotations

from collections.abc import Callable
from typing import Any, AnyStr, Literal, TYPE_CHECKING, TypedDict, Union

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
    from typing_extensions import Protocol

try:
    from typing import NotRequired
except ImportError:
    from typing_extensions import NotRequired


if TYPE_CHECKING:
    from attrs import AttrsInstance
    from msgspec import Struct
    from pydantic import BaseModel
    from pydantic.dataclasses import Dataclass


class DataclassProtocol(Protocol):
    __dataclass_fields__: dict
    __dataclass_params__: dict
    __post_init__: Callable | None


ModelTypes = Union["AttrsInstance", "BaseModel", "Dataclass", "DataclassProtocol", "Struct"]
Model = Union[ModelTypes, list[ModelTypes], dict[str, ModelTypes]]
ResponseValue = Union[QuartResponseValue, type[Model]]
HeadersValue = Union[QuartHeadersValue, Model]

ResponseReturnValue = (
    QuartResponseReturnValue
    | ResponseValue
    | tuple[ResponseValue, HeadersValue]
    | tuple[ResponseValue, StatusCode]
    | tuple[ResponseValue, StatusCode, HeadersValue]
)


class WebsocketProtocol(Protocol):
    async def receive_json(self) -> dict: ...

    async def send_json(self, data: dict) -> None: ...


class TestClientProtocol(Protocol):
    app: Quart

    async def _make_request(
        self,
        path: str,
        method: str,
        headers: dict | Headers | None,
        data: AnyStr | None,
        form: dict | None,
        files: dict[str, FileStorage] | None,
        query_string: dict | None,
        json: Any,
        scheme: str,
        root_path: str,
        http_version: str,
        scope_base: dict | None,
    ) -> Response: ...


class PydanticDumpOptions(TypedDict):
    by_alias: NotRequired[bool]
    exclude_defaults: NotRequired[bool]
    exclude_none: NotRequired[bool]
    exclude_unset: NotRequired[bool]
    round_trip: NotRequired[bool]
    serialize_as_any: NotRequired[bool]
    warnings: NotRequired[bool | Literal["none", "warn", "error"]]
