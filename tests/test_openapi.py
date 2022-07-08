from dataclasses import dataclass
from typing import Optional, Tuple

from quart import Quart

from quart_schema import (
    QuartSchema,
    validate_headers,
    validate_querystring,
    validate_request,
    validate_response,
)


@dataclass
class QueryItem:
    count_le: Optional[int] = None


@dataclass
class Details:
    name: str
    age: Optional[int] = None


@dataclass
class Result:
    name: str


@dataclass
class Headers:
    x_name: str


async def test_openapi() -> None:
    app = Quart(__name__)
    QuartSchema(app)

    @app.route("/")
    @validate_querystring(QueryItem)
    @validate_request(Details)
    @validate_headers(Headers)
    @validate_response(Result, 200, Headers)
    async def index() -> Tuple[Result, int, Headers]:
        """Summary
        Multi-line
        description.

        This is a new paragraph

            And this is an indented codeblock.

        And another paragraph."""
        return Result(name="bob"), 200, Headers(x_name="jeff")

    test_client = app.test_client()
    response = await test_client.get("/openapi.json")
    assert (await response.get_json()) == {
        "components": {"schemas": {}},
        "info": {"title": "test_openapi", "version": "0.1.0"},
        "openapi": "3.0.3",
        "paths": {
            "/": {
                "get": {
                    "summary": "Summary",
                    "description": "Multi-line\ndescription.\n\nThis is a new paragraph\n\n    And this is an indented "
                    "codeblock.\n\nAnd another paragraph.",
                    "parameters": [
                        {
                            "in": "query",
                            "name": "count_le",
                            "schema": {"title": "Count Le", "type": "integer"},
                        },
                        {
                            "in": "header",
                            "name": "x-name",
                            "schema": {"title": "X Name", "type": "string"},
                        },
                    ],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "properties": {
                                        "age": {"title": "Age", "type": "integer"},
                                        "name": {"title": "Name", "type": "string"},
                                    },
                                    "required": ["name"],
                                    "title": "Details",
                                    "type": "object",
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "properties": {"name": {"title": "Name", "type": "string"}},
                                        "required": ["name"],
                                        "title": "Result",
                                        "type": "object",
                                    }
                                },
                                "headers": {
                                    "x-name": {"schema": {"title": "X Name", "type": "string"}}
                                },
                            },
                            "description": "Result(name: str)",
                        }
                    },
                }
            }
        },
        "servers": [],
        "tags": [],
    }
