from typing import Dict, List, Optional, Tuple, Type

import pytest
from pydantic import Field
from pydantic.dataclasses import dataclass
from quart import Quart

from quart_schema import (
    deprecate,
    operation_id,
    QuartSchema,
    security_scheme,
    validate_headers,
    validate_querystring,
    validate_request,
    validate_response,
)
from quart_schema.typing import Model
from .helpers import ADetails, DCDetails, MDetails, PyDCDetails, PyDetails


@dataclass
class QueryItem:
    count_le: Optional[int] = Field(description="count_le description")


@dataclass
class Result:
    """Result"""

    name: str


@dataclass
class Headers:
    x_name: str = Field(
        ..., description="x-name description", json_schema_extra={"deprecated": True}
    )


@pytest.mark.parametrize(
    "type_, titles",
    [
        (ADetails, False),
        (DCDetails, True),
        (MDetails, False),
        (PyDetails, True),
        (PyDCDetails, True),
    ],
)
async def test_openapi(type_: Type[Model], titles: bool) -> None:
    app = Quart(__name__)
    QuartSchema(app)

    @app.get("/")
    @validate_querystring(QueryItem)
    @validate_headers(Headers)
    @validate_response(Result, 200, Headers)
    async def read_item() -> Tuple[Result, int, Headers]:
        """Summary
        Multi-line
        description.

        This is a new paragraph

            And this is an indented codeblock.

        And another paragraph."""
        return Result(name="bob"), 200, Headers(x_name="jeff")

    @app.post("/")
    @validate_request(type_)
    @validate_response(Result, 201, Headers)
    @operation_id("make_item")
    @deprecate()
    async def create_item() -> Tuple[Result, int, Headers]:
        return Result(name="bob"), 201, Headers(x_name="jeff")

    @app.websocket("/ws")
    async def ws() -> None:
        pass

    test_client = app.test_client()
    response = await test_client.get("/openapi.json")

    result = await response.get_json()

    expected = {
        "components": {"schemas": {}},
        "info": {"title": "tests.test_openapi", "version": "0.1.0"},
        "openapi": "3.1.0",
        "paths": {
            "/": {
                "get": {
                    "description": "Multi-line\n"
                    "description.\n"
                    "\n"
                    "This is a new paragraph\n"
                    "\n"
                    "    And this is an indented "
                    "codeblock.\n"
                    "\n"
                    "And another paragraph.",
                    "operationId": "get_read_item",
                    "parameters": [
                        {
                            "description": "count_le description",
                            "in": "query",
                            "name": "count_le",
                            "schema": {
                                "anyOf": [{"type": "integer"}, {"type": "null"}],
                                "title": "Count Le",
                            },
                        },
                        {
                            "deprecated": True,
                            "description": "x-name description",
                            "in": "header",
                            "name": "x-name",
                            "schema": {"title": "X Name", "type": "string"},
                        },
                    ],
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "description": "Result",
                                        "properties": {"name": {"title": "Name", "type": "string"}},
                                        "required": ["name"],
                                        "title": "Result",
                                        "type": "object",
                                    }
                                },
                                "headers": {
                                    "x-name": {
                                        "schema": {
                                            "deprecated": True,
                                            "description": "x-name " "description",
                                            "title": "X " "Name",
                                            "type": "string",
                                        }
                                    }
                                },
                            },
                            "description": "Result",
                        }
                    },
                    "summary": "Summary",
                },
                "post": {
                    "deprecated": True,
                    "operationId": "post_make_item",
                    "parameters": [],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "properties": {
                                        "age": {
                                            "anyOf": [{"type": "integer"}, {"type": "null"}],
                                            "default": None,
                                            "title": "Age",
                                        },
                                        "name": {"title": "Name", "type": "string"},
                                    },
                                    "required": ["name"],
                                    "title": type_.__name__,
                                    "type": "object",
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "description": "Result",
                                        "properties": {"name": {"title": "Name", "type": "string"}},
                                        "required": ["name"],
                                        "title": "Result",
                                        "type": "object",
                                    }
                                },
                                "headers": {
                                    "x-name": {
                                        "schema": {
                                            "deprecated": True,
                                            "description": "x-name " "description",
                                            "title": "X " "Name",
                                            "type": "string",
                                        }
                                    }
                                },
                            },
                            "description": "Result",
                        }
                    },
                },
            }
        },
    }
    if not titles:
        del expected["paths"]["/"]["post"]["requestBody"]["content"][  # type: ignore
            "application/json"
        ]["schema"]["properties"]["name"]["title"]
        del expected["paths"]["/"]["post"]["requestBody"]["content"][  # type: ignore
            "application/json"
        ]["schema"]["properties"]["age"]["title"]
    assert result == expected


async def test_security_schemes() -> None:
    app = Quart(__name__)
    QuartSchema(
        app,
        security_schemes={
            "MyBearer": {"type": "http", "scheme": "bearer"},
            "MyBasicAuth": {"type": "http", "scheme": "basic"},
            "MyAPI": {"type": "apiKey", "in_": "cookie", "name": "Bob"},
        },
        security=[{"MyBearer": []}, {"MyBasicAuth": ["foo", "bar"]}],
    )

    @app.route("/")
    @security_scheme([{"MyBearer": []}])
    async def index() -> Tuple[Dict, int]:
        return {}, 200

    test_client = app.test_client()
    response = await (await test_client.get("/openapi.json")).get_json()
    assert response["security"] == [{"MyBearer": []}, {"MyBasicAuth": ["foo", "bar"]}]
    assert response["components"]["securitySchemes"] == {
        "MyBearer": {"type": "http", "scheme": "bearer"},
        "MyBasicAuth": {"type": "http", "scheme": "basic"},
        "MyAPI": {"type": "apiKey", "in": "cookie", "name": "Bob"},
    }
    assert response["paths"]["/"]["get"]["security"] == [{"MyBearer": []}]


@dataclass
class Employee:
    name: str


@dataclass
class Employees:
    resources: List[Employee]


async def test_openapi_refs() -> None:
    app = Quart(__name__)
    QuartSchema(app, convert_casing=True)

    @app.route("/")
    @validate_response(Employees)
    async def index() -> Employees:
        return Employees(resources=[Employee(name="bob")])

    test_client = app.test_client()
    response = await test_client.get("/openapi.json")
    schema = await response.get_json()
    ref = schema["paths"]["/"]["get"]["responses"]["200"]["content"]["application/json"]["schema"][
        "properties"
    ]["resources"]["items"]["$ref"]
    assert ref[len("#/components/schemas/") :] in schema["components"]["schemas"].keys()
