from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from pydantic import Field
from quart import Quart

from quart_schema import (
    QuartSchema,
    security_scheme,
    validate_headers,
    validate_querystring,
    validate_request,
    validate_response,
)
from quart_schema.extension import deprecated


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
    x_name: str = Field(..., description="x-name description", deprecated=True)


async def test_openapi() -> None:
    app = Quart(__name__)
    QuartSchema(app)

    @app.route("/")
    @validate_querystring(QueryItem)
    @validate_request(Details)
    @validate_headers(Headers)
    @validate_response(Result, 200, Headers)
    @deprecated()
    async def index() -> Tuple[Result, int, Headers]:
        """Summary
        Multi-line
        description.

        This is a new paragraph

            And this is an indented codeblock.

        And another paragraph."""
        return Result(name="bob"), 200, Headers(x_name="jeff")

    @app.websocket("/ws")
    async def ws() -> None:
        pass

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
                    "description": "Multi-line\ndescription.\n\nThis is a new paragraph\n\n    "
                    "And this is an indented codeblock.\n\nAnd another paragraph.",
                    "deprecated": True,
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
                            "deprecated": True,
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
                                            "deprecated": True
                                        }
                                    }
                                },
                            },
                            "description": "",
                        }
                    },
                }
            }
        },
    }


async def test_security_schemes() -> None:
    app = Quart(__name__)
    QuartSchema(
        app,
        security_schemes={
            "MyBearer": {"type": "http", "scheme": "bearer"},
            "MyBasicAuth": {"type": "http", "scheme": "basic"},
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
