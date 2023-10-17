from dataclasses import dataclass
from io import BytesIO
from typing import Any, List, Optional, Tuple, TypeVar, Union

import pytest
from pydantic import BaseModel, RootModel
from pydantic.dataclasses import dataclass as pydantic_dataclass
from pydantic.functional_validators import BeforeValidator
from quart import Quart, redirect, websocket
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

try:
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated  # type: ignore


@dataclass
class DCDetails:
    name: str
    age: Optional[int] = None


@dataclass
class DCItem:
    count: int
    details: DCDetails


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


class Details(BaseModel):
    name: str
    age: Optional[int] = None


class Item(BaseModel):
    count: int
    details: Details


class ItemCollection(RootModel):
    root: list[Item]


@pydantic_dataclass
class PyDCDetails:
    name: str
    age: Optional[int] = None


@pydantic_dataclass
class PyDCItem:
    count: int
    details: PyDCDetails


VALID_DICT = {"count": 2, "details": {"name": "bob"}}
INVALID_DICT = {"count": 2, "name": "bob"}
VALID = Item(count=2, details=Details(name="bob"))
INVALID = Details(name="bob")
VALID_COLLECTION = [Item(count=2, details=Details(name="bob")), Item(count=3, details=Details(name="jane"))]
INVALID_COLLECTION = ["list", "of", "strings", "not", "items"]
VALID_DC = DCItem(count=2, details=DCDetails(name="bob"))
INVALID_DC = DCDetails(name="bob")
VALID_PyDC = PyDCItem(count=2, details=PyDCDetails(name="bob"))
INVALID_PyDC = PyDCDetails(name="bob")


@pytest.mark.parametrize("path", ["/", "/dc", "/pydc"])
@pytest.mark.parametrize(
    "json, status",
    [
        (VALID_DICT, 200),
        (INVALID_DICT, 400),
    ],
)
async def test_request_validation(path: str, json: dict, status: int) -> None:
    app = Quart(__name__)
    QuartSchema(app)

    @app.route("/", methods=["POST"])
    @validate_request(Item)
    async def item(data: Item) -> ResponseReturnValue:
        return ""

    @app.route("/dc", methods=["POST"])
    @validate_request(DCItem)
    async def dcitem(data: DCItem) -> ResponseReturnValue:
        return ""

    @app.route("/pydc", methods=["POST"])
    @validate_request(PyDCItem)
    async def pydcitem(data: PyDCItem) -> ResponseReturnValue:
        return ""

    test_client = app.test_client()
    response = await test_client.post(path, json=json)
    assert response.status_code == status


@pytest.mark.parametrize(
    "data, status",
    [
        ({"name": "bob"}, 200),
        ({"age": 2}, 400),
    ],
)
async def test_request_form_validation(data: dict, status: int) -> None:
    app = Quart(__name__)
    QuartSchema(app)

    @app.route("/", methods=["POST"])
    @validate_request(Details, source=DataSource.FORM)
    async def item(data: Details) -> ResponseReturnValue:
        return ""

    test_client = app.test_client()
    response = await test_client.post("/", form=data)
    assert response.status_code == status


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
    assert (await response.get_data()) == b"ABC"  # type: ignore


@pytest.mark.parametrize(
    "model, return_value, status",
    [
        (Item, VALID_DICT, 200),
        (Item, INVALID_DICT, 500),
        (Item, VALID, 200),
        (Item, INVALID, 500),
        (ItemCollection, VALID_COLLECTION, 200),
        (ItemCollection, INVALID_COLLECTION, 500),
        (RootModel[list[Item]], VALID_COLLECTION, 200),
        (RootModel[list[Item]], INVALID_COLLECTION, 500),
        (list[Item], VALID_COLLECTION, 200),
        (list[Item], INVALID_COLLECTION, 500),
        (DCItem, VALID_DICT, 200),
        (DCItem, INVALID_DICT, 500),
        (DCItem, VALID_DC, 200),
        (DCItem, INVALID_DC, 500),
        (PyDCItem, VALID_DICT, 200),
        (PyDCItem, INVALID_DICT, 500),
        (PyDCItem, VALID_PyDC, 200),
        (PyDCItem, INVALID_PyDC, 500),
    ],
)
async def test_response_validation(model: Any, return_value: Any, status: int) -> None:
    app = Quart(__name__)
    QuartSchema(app)

    @app.route("/")
    @validate_response(model)
    async def item() -> ResponseReturnValue:
        return return_value

    test_client = app.test_client()
    response = await test_client.get("/")
    assert response.status_code == status


async def test_redirect_validation() -> None:
    app = Quart(__name__)
    QuartSchema(app)

    @app.route("/")
    @validate_response(Item)
    async def item() -> ResponseReturnValue:
        return redirect("/b")

    test_client = app.test_client()
    response = await test_client.get("/")
    assert response.status_code == 302


@pytest.mark.parametrize(
    "return_value, status",
    [
        (VALID_DICT, 200),
        (INVALID_DICT, 500),
    ],
)
async def test_view_response_validation(return_value: Any, status: int) -> None:
    class ValidatedView(View):
        decorators = [validate_response(Item)]
        methods = ["GET"]

        def dispatch_request(self, **kwargs: Any) -> ResponseReturnValue:  # type: ignore
            return return_value

    app = Quart(__name__)
    QuartSchema(app)

    app.add_url_rule("/", view_func=ValidatedView.as_view("view"))

    test_client = app.test_client()
    response = await test_client.get("/")
    assert response.status_code == status


async def test_websocket_validation() -> None:
    app = Quart(__name__)
    QuartSchema(app)

    @app.websocket("/ws")
    async def ws() -> None:
        await websocket.receive_as(Item)  # type: ignore
        with pytest.raises(SchemaValidationError):
            await websocket.receive_as(Item)  # type: ignore
        await websocket.send_as(VALID_DICT, Item)  # type: ignore
        with pytest.raises(SchemaValidationError):
            await websocket.send_as(VALID_DICT, Details)  # type: ignore

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


@dataclass
class DCHeaders:
    x_required: str
    x_optional: Optional[int] = None


class Headers(BaseModel):
    x_required: str
    x_optional: Optional[int] = None


@pytest.mark.parametrize("model", [DCHeaders, Headers])
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
