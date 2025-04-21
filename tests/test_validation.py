import sys
from dataclasses import dataclass
from io import BytesIO
from typing import Annotated, Any, List, Literal, Optional, Tuple, Type, TypeVar, Union

import pytest
from attrs import define
from msgspec import Struct
from pydantic import BaseModel
from pydantic.dataclasses import dataclass as pydantic_dataclass
from pydantic.functional_validators import BeforeValidator
from quart import Quart, redirect, Response, websocket
from quart.datastructures import FileStorage
from quart.views import View

from quart_schema import (
    DataSource,
    QuartSchema,
    ResponseReturnValue,
    SchemaValidationError,
    validate_headers,
    validate_querystring,
    validate_request,
    validate_response,
)
from quart_schema.pydantic import File
from .helpers import ADetails, DCDetails, MDetails, PyDCDetails, PyDetails, TDetails

if sys.version_info >= (3, 12):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict


@define
class AItem:
    count: int
    details: ADetails


class MItem(Struct):
    count: int
    details: MDetails


@dataclass
class DCItem:
    count: int
    details: DCDetails


class PyItem(BaseModel):
    count: int
    details: PyDetails


@pydantic_dataclass
class PyDCItem:
    count: int
    details: PyDCDetails


class TItem(TypedDict):
    count: int
    details: TDetails


class FileInfo(BaseModel):
    upload: File


T = TypeVar("T")


def _to_list(value: Union[T, List[T]]) -> List[T]:
    if isinstance(value, list):
        return value
    else:
        return [value]


class QueryItem(BaseModel):
    count_le: Optional[int] = None
    count_gt: Optional[int] = None
    keys: Annotated[Optional[List[int]], BeforeValidator(_to_list)] = None


VALID_DICT = {"count": 2, "details": {"name": "bob"}}
INVALID_DICT = {"count": 2, "name": "bob"}


@pytest.mark.parametrize("type_", [AItem, DCItem, MItem, PyItem, PyDCItem, TItem])
@pytest.mark.parametrize(
    "json, status",
    [
        (VALID_DICT, 200),
        (INVALID_DICT, 400),
    ],
)
async def test_request_validation(
    type_: Type[Union[AItem, DCItem, MItem, PyItem, PyDCItem, TItem]],
    json: dict,
    status: int,
) -> None:
    app = Quart(__name__)
    QuartSchema(app)

    @app.route("/", methods=["POST"])
    @validate_request(type_)
    async def item(data: Any) -> ResponseReturnValue:
        return ""

    test_client = app.test_client()
    response = await test_client.post("/", json=json)
    assert response.status_code == status


@pytest.mark.parametrize("type_", [ADetails, DCDetails, MDetails, PyDetails, PyDCDetails, TDetails])
@pytest.mark.parametrize(
    "data, status",
    [
        ({"name": "bob"}, 200),
        ({"age": 2}, 400),
    ],
)
async def test_request_form_validation(
    type_: Type[Union[ADetails, DCDetails, MDetails, PyDetails, PyDCDetails, TDetails]],
    data: dict,
    status: int,
) -> None:
    app = Quart(__name__)
    QuartSchema(app)

    @app.route("/", methods=["POST"])
    @validate_request(type_, source=DataSource.FORM)
    async def item(data: Any) -> ResponseReturnValue:
        return ""

    test_client = app.test_client()
    response = await test_client.post("/", form=data)
    assert response.status_code == status


class MultiItem(BaseModel):
    multi: List[int]
    single: int


async def test_request_form_validation_multi() -> None:
    app = Quart(__name__)
    QuartSchema(app)

    @app.route("/", methods=["POST"])
    @validate_request(MultiItem, source=DataSource.FORM)
    async def item(data: MultiItem) -> MultiItem:
        return data

    test_client = app.test_client()
    response = await test_client.post(
        "/",
        data=b"multi=1&multi=2&single=2",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    assert await response.get_json() == {"multi": [1, 2], "single": 2}


async def test_request_file_validation() -> None:
    app = Quart(__name__)
    QuartSchema(app)

    @app.route("/", methods=["POST"])
    @validate_request(FileInfo, source=DataSource.FORM_MULTIPART)
    async def item(data: FileInfo) -> ResponseReturnValue:
        return data.upload.read()

    test_client = app.test_client()
    response = await test_client.post(
        "/", files={"upload": FileStorage(stream=BytesIO(b"ABC"), filename="bob")}
    )
    assert response.status_code == 200
    assert (await response.get_data()) == b"ABC"


@pytest.mark.parametrize("type_", [AItem, DCItem, MItem, PyItem, PyDCItem, TItem])
@pytest.mark.parametrize(
    "return_value, status",
    [
        (VALID_DICT, 200),
        (INVALID_DICT, 500),
    ],
)
async def test_response_validation(
    type_: Type[Union[AItem, DCItem, MItem, PyItem, PyDCItem, TItem]],
    return_value: Any,
    status: int,
) -> None:
    app = Quart(__name__)
    QuartSchema(app)

    @app.route("/")
    @validate_response(type_)
    async def item() -> ResponseReturnValue:
        return return_value

    test_client = app.test_client()
    response = await test_client.get("/")
    assert response.status_code == status


@pytest.mark.parametrize(
    "type_, preference",
    [
        (AItem, "msgspec"),
        (DCItem, "msgspec"),
        (MItem, "msgspec"),
        (DCItem, "pydantic"),
        (PyItem, "pydantic"),
        (PyDCItem, "pydantic"),
        (TItem, "pydantic"),
    ],
)
@pytest.mark.parametrize(
    "return_value, status",
    [
        (VALID_DICT, 200),
        (INVALID_DICT, 500),
    ],
)
async def test_response_list_validation(
    type_: Type[Union[AItem, DCItem, MItem, PyItem, PyDCItem, TItem]],
    preference: Literal["msgspec", "pydantic"],
    return_value: Any,
    status: int,
) -> None:
    app = Quart(__name__)
    QuartSchema(app, conversion_preference=preference)

    @app.route("/")
    @validate_response(List[type_])  # type: ignore
    async def item() -> ResponseReturnValue:
        return [return_value]

    test_client = app.test_client()
    response = await test_client.get("/")
    assert response.status_code == status


async def test_redirect_validation() -> None:
    app = Quart(__name__)
    QuartSchema(app)

    @app.route("/")
    @validate_response(PyItem)
    async def item() -> ResponseReturnValue:
        return redirect("/b")

    test_client = app.test_client()
    response = await test_client.get("/")
    assert response.status_code == 302


async def test_response_validation_of_response() -> None:
    app = Quart(__name__)
    QuartSchema(app)

    @app.route("/")
    @validate_response(PyItem)
    async def item() -> ResponseReturnValue:
        return Response(b"", status=200)

    test_client = app.test_client()
    response = await test_client.get("/")
    assert response.status_code == 500


@pytest.mark.parametrize(
    "return_value, status",
    [
        (VALID_DICT, 200),
        (INVALID_DICT, 500),
    ],
)
async def test_view_response_validation(return_value: Any, status: int) -> None:
    class ValidatedView(View):
        decorators = [validate_response(PyItem)]
        methods = ["GET"]

        def dispatch_request(self, **kwargs: Any) -> ResponseReturnValue:  # type: ignore
            return return_value

    app = Quart(__name__)
    QuartSchema(app)

    app.add_url_rule("/", view_func=ValidatedView.as_view("view"))

    test_client = app.test_client()
    response = await test_client.get("/")
    assert response.status_code == status


@pytest.mark.parametrize("type_", [AItem, DCItem, MItem, PyItem, PyDCItem, TItem])
async def test_websocket_validation(
    type_: Type[Union[AItem, DCItem, MItem, PyItem, PyDCItem, TItem]],
) -> None:
    app = Quart(__name__)
    QuartSchema(app)

    @app.websocket("/ws")
    async def ws() -> None:
        await websocket.receive_as(type_)  # type: ignore
        with pytest.raises(SchemaValidationError):
            await websocket.receive_as(type_)  # type: ignore
        await websocket.send_as(VALID_DICT, type_)  # type: ignore
        with pytest.raises(SchemaValidationError):
            await websocket.send_as(INVALID_DICT, type_)  # type: ignore

    test_client = app.test_client()
    async with test_client.websocket("/ws") as test_websocket:
        await test_websocket.send_json(VALID_DICT)
        await test_websocket.send_json(INVALID_DICT)


@pytest.mark.parametrize(
    "path, status",
    [
        ("/", 200),
        ("/?count_le=2", 200),
        ("/?count_le=2&count_gt=0", 200),
        ("/?count_le=a", 400),
        ("/?count=a", 200),
        ("/?keys=1&keys=2", 200),
        ("/?keys=1", 200),
    ],
)
async def test_querystring_validation(path: str, status: int) -> None:
    app = Quart(__name__)
    QuartSchema(app)

    @app.route("/")
    @validate_querystring(QueryItem)
    async def query_item(query_args: QueryItem) -> ResponseReturnValue:
        return ""

    test_client = app.test_client()
    response = await test_client.get(path)
    assert response.status_code == status


@pydantic_dataclass
class PyDCHeaders:
    x_required: str
    x_optional: Optional[int] = None


class Headers(BaseModel):
    x_required: str
    x_optional: Optional[int] = None


@pytest.mark.parametrize("model", [PyDCHeaders, Headers])
@pytest.mark.parametrize(
    "request_headers, status",
    [
        ({"X-Required": "abc", "X-Optional": "2"}, 200),
        ({"X-Required": "abc", "User-Agent": "abc"}, 200),
        ({}, 400),
        ({"X-Required": "abc", "X-Optional": "abc"}, 400),
        ({"X-Optional": "2"}, 400),
    ],
)
async def test_request_header_validation(model: Any, request_headers: dict, status: int) -> None:
    app = Quart(__name__)
    QuartSchema(app)

    @app.route("/")
    @validate_headers(model)
    async def headers_item(headers: Any) -> ResponseReturnValue:
        return ""

    test_client = app.test_client()
    response = await test_client.get("/", headers=request_headers)
    assert response.status_code == status


@pytest.mark.parametrize(
    "response_headers, status",
    [
        ({"X-Required": "abc", "X-Optional": "2"}, 200),
        ({"X-Required": "abc", "User-Agent": "abc"}, 200),
        (Headers(x_required="abc"), 200),
        ({}, 500),
        ({"X-Required": "abc", "X-Optional": "abc"}, 500),
        ({"X-Optional": "2"}, 500),
    ],
)
async def test_response_header_validation(response_headers: dict, status: int) -> None:
    app = Quart(__name__)
    QuartSchema(app)

    @app.route("/")
    @validate_response(DCItem, 200, Headers)
    async def headers_item() -> Tuple[dict, int, Union[dict, Headers]]:
        return VALID_DICT, 200, response_headers

    test_client = app.test_client()
    response = await test_client.get("/")
    assert response.status_code == status
