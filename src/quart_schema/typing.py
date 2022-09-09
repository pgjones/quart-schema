from __future__ import annotations

from typing import Any, AnyStr, Dict, List, Optional, Tuple, Type, TYPE_CHECKING, TypeVar, Union

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
    from typing import Literal, Protocol, TypedDict
except ImportError:
    from typing_extensions import Literal, Protocol, TypedDict  # type: ignore


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


class ExternalDocumentationObject(TypedDict, total=False):
    description: str
    url: str


class TagObject(TypedDict, total=False):
    name: str
    description: str
    externalDocs: ExternalDocumentationObject  # noqa: N815


class VariableObject(TypedDict, total=False):
    enum: List[str]
    default: str
    description: str


class ServerObject(TypedDict, total=False):
    url: str
    description: str
    variables: Dict[str, VariableObject]


SecuritySchemeObject = TypedDict(
    "SecuritySchemeObject",
    {
        "type": Literal["apiKey", "http", "mutualTLS", "oauth2", "openIdConnect"],
        "description": str,
        "name": str,
        "in": Literal["query", "header", "cookie"],
        "scheme": str,
        "bearerFormat": str,
        "openIdConnectUrl": str,
        "flows": dict,
    },
    total=False,
)
