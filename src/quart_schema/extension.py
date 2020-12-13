from __future__ import annotations

import re
from dataclasses import asdict, is_dataclass
from types import new_class
from typing import Any, cast, Dict, Optional, overload, Type, Union

from pydantic import ValidationError
from pydantic.json import pydantic_encoder
from quart import Quart, render_template_string
from quart.json import JSONEncoder as QuartJSONEncoder
from quart.wrappers import Websocket

from .typing import BM, DC, WebsocketProtocol
from .validation import (
    QUART_SCHEMA_QUERYSTRING_ATTRIBUTE,
    QUART_SCHEMA_REQUEST_ATTRIBUTE,
    QUART_SCHEMA_RESPONSE_ATTRIBUTE,
)

PATH_RE = re.compile("<(?:[^:]*:)?([^>]+)>")

DOCS_TEMPLATE = """
<head>
  <link type="text/css" rel="stylesheet" href="{{ swagger_css_url }}">
  <title>{{ title }}</title>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="{{ swagger_js_url }}"></script>
  <script>
    const ui = SwaggerUIBundle({
      deepLinking: true,
      dom_id: "#swagger-ui",
      layout: "BaseLayout",
      presets: [
        SwaggerUIBundle.presets.apis,
        SwaggerUIBundle.SwaggerUIStandalonePreset
      ],
      showExtensions: true,
      showCommonExtensions: true,
      url: "{{ openapi_path }}"
    });
  </script>
</body>
"""


class SchemaValidationError(Exception):
    pass


class WebsocketMixin:
    @overload
    async def receive_as(self: WebsocketProtocol, model_class: Type[BM]) -> BM:
        ...

    @overload
    async def receive_as(self: WebsocketProtocol, model_class: Type[DC]) -> DC:
        ...

    async def receive_as(
        self: WebsocketProtocol, model_class: Union[Type[BM], Type[DC]]
    ) -> Union[BM, DC]:
        data = await self.receive_json()
        try:
            return model_class(**data)
        except ValidationError:
            raise SchemaValidationError()

    async def send_as(
        self: WebsocketProtocol, value: Any, model_class: Union[Type[BM], Type[DC]]
    ) -> None:
        if isinstance(value, dict):
            try:
                model_value = model_class(**value)
            except ValidationError:
                raise SchemaValidationError()
        elif type(value) == model_class:
            model_value = value
        else:
            raise SchemaValidationError()
        if is_dataclass(model_value):
            data = asdict(model_value)
        else:
            model_value = cast(BM, model_value)
            data = model_value.dict()
        await self.send_json(data)


class JSONEncoder(QuartJSONEncoder):
    def default(self, object_: Any) -> Any:
        return pydantic_encoder(object_)


class QuartSchema:
    def __init__(
        self,
        app: Optional[Quart] = None,
        *,
        openapi_path: Optional[str] = "/openapi.json",
        docs_path: Optional[str] = "/docs",
        title: Optional[str] = None,
        version: str = "0.1.0",
    ) -> None:
        self.openapi_path = openapi_path
        self.docs_path = docs_path
        self.title = title
        self.version = version
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Quart) -> None:
        self.app = app
        self.title = self.app.name if self.title is None else self.title
        app.websocket_class = new_class("Websocket", (Websocket, WebsocketMixin))  # type: ignore
        app.json_encoder = JSONEncoder
        if self.openapi_path is not None:
            self.app.add_url_rule(self.openapi_path, "openapi", self.openapi)
        if self.docs_path is not None:
            self.app.add_url_rule(self.docs_path, "docs", self.docs)

    async def openapi(self) -> dict:
        paths: Dict[str, dict] = {}
        for rule in self.app.url_map.iter_rules():
            func = self.app.view_functions[rule.endpoint]
            response_schemas = getattr(func, QUART_SCHEMA_RESPONSE_ATTRIBUTE, {})
            request_schema = getattr(func, QUART_SCHEMA_REQUEST_ATTRIBUTE, None)
            querystring_schema = getattr(func, QUART_SCHEMA_QUERYSTRING_ATTRIBUTE, None)
            if response_schemas == {} and request_schema is None and querystring_schema is None:
                continue

            path_object = {  # type: ignore
                "description": func.__doc__,
                "parameters": [],
                "responses": {},
            }
            for status_code, schema in response_schemas.items():
                path_object["responses"][status_code] = {  # type: ignore
                    "content": {
                        "application/json": {
                            "schema": schema,
                        },
                    },
                }

            if request_schema is not None:
                path_object["requestBody"] = {
                    "content": {
                        "application/json": {
                            "schema": request_schema,
                        },
                    },
                }

            if querystring_schema is not None:
                for name, type_ in querystring_schema["properties"].items():
                    path_object["parameters"].append(  # type: ignore
                        {
                            "name": name,
                            "in": "query",
                            "schema": type_,
                        }
                    )

            for name, converter in rule._converters.items():
                path_object["parameters"].append(  # type: ignore
                    {
                        "name": name,
                        "in": "path",
                    }
                )

            path = re.sub(PATH_RE, r"{\1}", rule.rule)
            paths.setdefault(path, {})

            for method in rule.methods:
                if method == "HEAD" or (method == "OPTIONS" and rule.provide_automatic_options):
                    continue
                paths[path][method.lower()] = path_object

        return {
            "openapi": "3.0.3",
            "info": {
                "title": self.title,
                "version": self.version,
            },
            "paths": paths,
        }

    async def docs(self) -> str:
        return await render_template_string(
            DOCS_TEMPLATE,
            title=self.title,
            openapi_path=self.openapi_path,
            swagger_js_url="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/3.37.2/swagger-ui-bundle.js",  # noqa: E501
            swagger_css_url="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/3.37.2/swagger-ui.min.css",  # noqa: E501
        )
