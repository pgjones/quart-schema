from __future__ import annotations

from dataclasses import asdict, is_dataclass
from functools import wraps
from types import new_class
from typing import Any, Callable, cast, Dict, Optional, overload, Type, TypeVar, Union

from pydantic import BaseModel, ValidationError
from pydantic.json import pydantic_encoder
from quart import Quart, render_template_string, request
from quart.exceptions import BadRequest
from quart.json import JSONEncoder as QuartJSONEncoder
from quart.wrappers import Websocket
from werkzeug.datastructures import Headers

try:
    from typing import Protocol
except ImportError:
    from typing_extensions import Protocol  # type: ignore


class Dataclass(Protocol):
    __pydantic_model__: Type[BaseModel]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        ...


class WebsocketProtocol(Protocol):
    async def receive_json(self) -> dict:
        ...

    async def send_json(self, data: dict) -> None:
        ...


class JSONEncoder(QuartJSONEncoder):
    def default(self, object_: Any) -> Any:
        return pydantic_encoder(object_)


BM = TypeVar("BM", bound=BaseModel)
DC = TypeVar("DC", bound=Dataclass)

QUART_SCHEMA_REQUEST_ATTRIBUTE = "_quart_schema_request_schema"
QUART_SCHEMA_RESPONSE_ATTRIBUTE = "_quart_schema_response_schemas"

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


class ResponseSchemaValidationError(Exception):
    pass


class RequestSchemaValidationError(BadRequest):
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
            path = {
                "description": func.__doc__,
                "responses": {},
            }
            response_schemas = getattr(func, QUART_SCHEMA_RESPONSE_ATTRIBUTE, {})
            for status_code, schema in response_schemas.items():
                path["responses"][status_code] = {  # type: ignore
                    "content": {
                        "application/json": {
                            "schema": schema,
                        },
                    },
                }
            request_schema = getattr(func, QUART_SCHEMA_REQUEST_ATTRIBUTE, None)
            if request_schema is not None:
                path["requestBody"] = {
                    "content": {
                        "application/json": {
                            "schema": request_schema,
                        },
                    },
                }
            paths[rule.rule] = {}
            for method in rule.methods:
                if method == "HEAD" or (method == "OPTIONS" and rule.provide_automatic_options):
                    continue
                paths[rule.rule][method.lower()] = path

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


def validate_request(model_class: Union[Type[BaseModel], Type[Dataclass]]) -> Callable:
    schema = getattr(model_class, "__pydantic_model__", model_class).schema()

    def decorator(func: Callable) -> Callable:
        setattr(func, QUART_SCHEMA_REQUEST_ATTRIBUTE, schema)

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            data = await request.get_json()
            try:
                model = model_class(**data)
            except (TypeError, ValidationError):
                raise RequestSchemaValidationError()
            else:
                return await func(*args, data=model, **kwargs)

        return wrapper

    return decorator


def validate_response(model_class: Union[Type[BM], Type[DC]], status_code: int = 200) -> Callable:
    schema = getattr(model_class, "__pydantic_model__", model_class).schema()

    def decorator(func: Callable) -> Callable:
        schemas = getattr(func, QUART_SCHEMA_RESPONSE_ATTRIBUTE, {})
        schemas[status_code] = schema
        setattr(func, QUART_SCHEMA_RESPONSE_ATTRIBUTE, schemas)

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = await func(*args, **kwargs)

            status_or_headers = None
            headers = None
            if isinstance(result, tuple):
                value, status_or_headers, headers = result + (None,) * (3 - len(result))
            else:
                value = result

            status = 200
            if status_or_headers is not None and not isinstance(
                status_or_headers, (Headers, dict, list)
            ):
                status = int(status_or_headers)

            if status in schemas:
                if isinstance(value, dict):
                    try:
                        model_value = model_class(**value)
                    except ValidationError:
                        raise ResponseSchemaValidationError()
                elif type(value) == model_class:
                    model_value = value
                else:
                    raise ResponseSchemaValidationError()
                if is_dataclass(model_value):
                    return asdict(model_value), status_or_headers, headers
                else:
                    model_value = cast(BM, model_value)
                    return model_value.dict(), status_or_headers, headers
            else:
                return result

        return wrapper

    return decorator
