from dataclasses import asdict, dataclass
from typing import Optional

from quart import Quart

from quart_schema import (
    QuartSchema,
    ResponseReturnValue,
    validate_querystring,
    validate_request,
    validate_response,
)


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
    snake_case: Optional[str] = None


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
