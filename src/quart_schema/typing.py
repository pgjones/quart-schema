from __future__ import annotations

from typing import Any, AnyStr, Dict, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel
from quart.datastructures import FileStorage
from quart.wrappers import Response
from werkzeug.datastructures import Headers

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
DC = TypeVar("DC", bound=Dataclass)


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
