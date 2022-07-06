from dataclasses import dataclass
from typing import Optional, Tuple

from pydantic import Field
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
    count_le: Optional[int] = Field(description="count_le description")


@dataclass
class Details:
    name: str
    age: Optional[int] = None


@dataclass
class Result:
    name: str


@dataclass
class Headers:
    x_name: str = Field(..., description="x-name description")


async def test_openapi() -> None:
    app = Quart(__name__)
    QuartSchema(app)

    @app.route("/")
    @validate_querystring(QueryItem)
    @validate_request(Details)
    @validate_headers(Headers)
    @validate_response(Result, 200, Headers)
    async def index() -> Tuple[Result, int, Headers]:
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
                    "parameters": [
                        {
                            "in": "query",
                            "name": "count_le",
                            "description": "count_le description",
                            "schema": {"title": "Count Le", "type": "integer"},
                        },
                        {
                            "in": "header",
                            "name": "x-name",
                            "description": "x-name description",
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
                                    "x-name": {
                                        "schema": {
                                            "title": "X Name",
                                            "type": "string",
                                            "description": "x-name description",
                                        }
                                    }
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
