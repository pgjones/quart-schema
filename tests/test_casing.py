from dataclasses import asdict, dataclass
from typing import Any

import pytest
from quart import Quart

from quart_schema import (
    camel_to_snake,
    kebab_to_snake,
    QuartSchema,
    ResponseReturnValue,
    snake_to_camel,
    snake_to_kebab,
    validate_querystring,
    validate_request,
    validate_response,
)


@pytest.mark.parametrize(
    "input, expected",
    [
        ("item2Value", "item2_value"),
        ("item2value", "item2value"),
        ("parseHTTPResponse", "parse_http_response"),
        ("HelloWorld", "hello_world"),
        ("get2FA", "get2_fa"),
        ("", ""),
    ],
)
def test_camel_to_snake(input: Any, expected: Any) -> None:
    assert camel_to_snake(input) == expected


@pytest.mark.parametrize(
    "input, expected",
    [
        ("item2_value", "item2Value"),
        ("item2value", "item2value"),
        ("parse_http_response", "parseHttpResponse"),
        ("hello_world", "helloWorld"),
        ("get_2fa", "get2fa"),
        ("", ""),
    ],
)
def test_snake_to_camel(input: Any, expected: Any) -> None:
    assert snake_to_camel(input) == expected


@pytest.mark.parametrize(
    "input, expected",
    [
        ("item2-value", "item2_value"),
        ("item2value", "item2value"),
        ("parse-http-response", "parse_http_response"),
        ("hello-world", "hello_world"),
        ("get2-fa", "get2_fa"),
        ("", ""),
        ("a--b", "a__b"),
    ],
)
def test_kebab_to_snake(input: Any, expected: Any) -> None:
    assert kebab_to_snake(input) == expected


@pytest.mark.parametrize(
    "input, expected",
    [
        ("item2_value", "item2-value"),
        ("item2value", "item2value"),
        ("parse_http_response", "parse-http-response"),
        ("hello_world", "hello-world"),
        ("get_2fa", "get-2fa"),
        ("", ""),
        ("a__b", "a--b"),
    ],
)
def test_snake_to_kebab(input: Any, expected: Any) -> None:
    assert snake_to_kebab(input) == expected


@dataclass
class Data:
    snake_case: str


async def test_request_casing() -> None:
    app = Quart(__name__)
    QuartSchema(app, convert_casing=True)

    @app.route("/", methods=["POST"])
    @validate_request(Data)
    async def index(data: Data) -> ResponseReturnValue:
        return str(asdict(data))

    test_client = app.test_client()
    response = await test_client.post("/", json={"snakeCase": "Hello"})
    assert await response.get_data(as_text=True) == "{'snake_case': 'Hello'}"


async def test_response_casing() -> None:
    app = Quart(__name__)
    QuartSchema(app, convert_casing=True)

    @app.route("/", methods=["GET"])
    @validate_response(Data)
    async def index() -> Data:
        return Data(snake_case="Hello")

    test_client = app.test_client()
    response = await test_client.get("/")
    assert await response.get_data(as_text=True) == '{"snakeCase":"Hello"}\n'


@dataclass
class QueryData:
    snake_case: str | None = None


async def test_querystring_casing() -> None:
    app = Quart(__name__)
    QuartSchema(app, convert_casing=True)

    @app.get("/")
    @validate_querystring(QueryData)
    async def index(query_args: QueryData) -> ResponseReturnValue:
        return str(asdict(query_args))

    test_client = app.test_client()
    response = await test_client.get("/", query_string={"snake_case": "Hello"})
    assert await response.get_data(as_text=True) == "{'snake_case': 'Hello'}"
    response = await test_client.get("/?snakeCase=Hello")
    assert await response.get_data(as_text=True) == "{'snake_case': 'Hello'}"
