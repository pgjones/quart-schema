from __future__ import annotations

from typing import (
    Any,
    AnyStr,
    Callable,
    Dict,
    Iterable,
    Optional,
    Tuple,
    Type,
    TYPE_CHECKING,
    TypeVar,
    Union,
)

from pydantic import BaseModel
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
    ) -> Response:
        ...


class File(FileStorage):
    @classmethod
    def __get_validators__(self: Type["File"]) -> Iterable[Callable[..., Any]]:
        yield self.validate

    @classmethod
    def validate(self: Type["File"], v: Any) -> Any:
        if not isinstance(v, FileStorage):
            raise ValueError(f"Expected FileStorage, received: {type(v)}")
        return v

    @classmethod
    def __modify_schema__(self, field_schema: dict[str, Any]) -> None:
        field_schema.update({"type": "string", "format": "binary"})


def has_files(schema: Dict[str, Any]) -> tuple[bool, list[str]]:
    """Checks if the JSON schema has any File or list[File] fields

    Returns true/false and the names of the list[File] fields

    Arguments:
        schema: JSON schema dict, as returned by model_schema()
    """
    any_files = False
    file_lists = []
    for field, props in schema["properties"].items():
        is_list = False
        if props.get("type", "") == "array":
            props = props.get("items", {})
            is_list = True

        if props.get("type", "") == "string" and props.get("format", "") == "binary":
            any_files = True
            if is_list:
                file_lists.append(field)

    return (any_files, file_lists)


BM = TypeVar("BM", bound=BaseModel)
DC = TypeVar("DC", bound="Dataclass")
