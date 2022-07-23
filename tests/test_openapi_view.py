from dataclasses import dataclass
from typing import Optional, Tuple

from pydantic import Field
from quart import Quart
from quart.views import MethodView

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


def attach_test_view(app: Quart) -> None:
    test_api = TestView.as_view("test_api")
    app.add_url_rule(
        "/view",
        view_func=test_api,
        methods=["PUT"],
    )


class TestView(MethodView):
    @validate_querystring(QueryItem)
    @validate_request(Details)
    @validate_headers(Headers)
    @validate_response(Result, 200, Headers)
    def put(self, data: Details) -> Tuple[Result, int, Headers]:
        return Result(name="bob"), 200, Headers(x_name="jeff")


async def test_openapi_view() -> None:
    app = Quart(__name__)
    attach_test_view(app)
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
    response_json = await response.get_json()
    assert response_json == {
        "components": {"schemas": {}},
        "info": {"title": "test_openapi_view", "version": "0.1.0"},
        "openapi": "3.0.3",
        "paths": {
            "/": {
                "get": {
                    "description": "Multi-line\ndescription.\n\nThis is a new paragraph\n\n    "
                    "And this is an indented codeblock.\n\nAnd another paragraph.",
                    "parameters": [
                        {
                            "description": "count_le description",
                            "in": "query",
                            "name": "count_le",
                            "schema": {"title": "Count Le", "type": "integer"},
                        },
                        {
                            "description": "x-name description",
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
                                    "x-name": {
                                        "schema": {
                                            "description": "x-name description",
                                            "title": "X Name",
                                            "type": "string",
                                        }
                                    }
                                },
                            },
                            "description": "Result(name: str)",
                        }
                    },
                    "summary": "Summary",
                }
            },
            "/view": {
                "put": {
                    "parameters": [
                        {
                            "description": "count_le description",
                            "in": "query",
                            "name": "count_le",
                            "schema": {"title": "Count Le", "type": "integer"},
                        },
                        {
                            "description": "x-name description",
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
                                    "x-name": {
                                        "schema": {
                                            "description": "x-name description",
                                            "title": "X Name",
                                            "type": "string",
                                        }
                                    }
                                },
                            },
                            "description": "Result(name: str)",
                        }
                    },
                }
            },
        },
        "servers": [],
        "tags": [],
    }
