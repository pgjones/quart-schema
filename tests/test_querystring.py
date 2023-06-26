from dataclasses import dataclass, field

import pytest

from quart import Quart
from quart_schema import (
    QuartSchema,
    ResponseReturnValue,
    validate_querystring,
)


@dataclass
class QueryArgs:
    key: list[str] = field(default_factory=list)


@pytest.mark.parametrize(
    "path, status, res",
    [
        ("/", 200, {"key": []}),
        ("/?key=foo", 200, {"key": ["foo"]}),
        ("/?key=foo&key=bar", 200, {"key": ["foo", "bar"]}),
    ],
)
async def test_querystring_validation(path: str, status: int, res: dict[str, list[str]]) -> None:
    app = Quart(__name__)
    QuartSchema(app)

    @app.route("/")
    @validate_querystring(QueryArgs)
    async def query_item(query_args: QueryArgs) -> ResponseReturnValue:
        return query_args

    test_client = app.test_client()
    response = await test_client.get(path)
    assert response.status_code == status
    assert (await response.json) == res
