from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, AnyStr, cast, Dict, Optional, overload, Tuple, Type, Union

from humps import camelize, decamelize
from pydantic import BaseModel, ValidationError
from quart import current_app, Response
from quart.datastructures import FileStorage
from quart.testing.utils import sentinel
from werkzeug.datastructures import Authorization, Headers

from .typing import BM, DC, TestClientProtocol, WebsocketProtocol


class SchemaValidationError(Exception):
    def __init__(self, validation_error: Optional[ValidationError] = None) -> None:
        super().__init__()
        self.validation_error = validation_error


class WebsocketMixin:
    @overload
    async def receive_as(self: WebsocketProtocol, model_class: Type[BM]) -> BM:
        ...

    @overload
    async def receive_as(self: WebsocketProtocol, model_class: Type[DC]) -> DC:
        ...

    async def receive_as(  # type: ignore[misc]
        self: WebsocketProtocol, model_class: Union[Type[BM], Type[DC]]
    ) -> Union[BM, DC]:
        data = await self.receive_json()
        if current_app.config["QUART_SCHEMA_CONVERT_CASING"]:
            data = decamelize(data)
        try:
            return model_class(**data)
        except ValidationError as error:
            raise SchemaValidationError(error)

    async def send_as(
        self: WebsocketProtocol, value: Any, model_class: Union[Type[BM], Type[DC]]
    ) -> None:
        if isinstance(value, dict):
            try:
                model_value = model_class(**value)
            except ValidationError as error:
                raise SchemaValidationError(error)
        elif type(value) == model_class:  # noqa: E721
            model_value = value
        else:
            raise SchemaValidationError()
        if is_dataclass(model_value):
            data = asdict(model_value)  # type: ignore[arg-type]
        else:
            model_value = cast(BM, model_value)
            data = model_value.model_dump()
        if current_app.config["QUART_SCHEMA_CONVERT_CASING"]:
            data = camelize(data)
        await self.send_json(data)


class TestClientMixin:
    async def _make_request(
        self: TestClientProtocol,
        path: str,
        method: str,
        headers: Optional[Union[dict, Headers]],
        data: Optional[AnyStr],
        form: Optional[dict],
        files: Optional[Dict[str, FileStorage]],
        query_string: Optional[dict],
        json: Any,
        scheme: str,
        root_path: str,
        http_version: str,
        scope_base: Optional[dict],
        auth: Optional[Union[Authorization, Tuple[str, str]]] = None,
        subdomain: Optional[str] = None,
    ) -> Response:
        if json is not sentinel:
            was_model = False
            if is_dataclass(json):
                json = asdict(json)
                was_model = True
            elif isinstance(json, BaseModel):
                json = json.model_dump()
                was_model = True

            if was_model and self.app.config["QUART_SCHEMA_CONVERT_CASING"]:
                json = camelize(json)

        if form is not None:
            was_model = False
            if is_dataclass(form):
                form = asdict(form)  # type: ignore[arg-type]
                was_model = True
            elif isinstance(form, BaseModel):
                form = form.model_dump()
                was_model = True

            if was_model and self.app.config["QUART_SCHEMA_CONVERT_CASING"]:
                form = camelize(form)

        if query_string is not None:
            was_model = False
            if is_dataclass(query_string):
                query_string = asdict(query_string)  # type: ignore[arg-type]
                was_model = True
            elif isinstance(query_string, BaseModel):
                query_string = query_string.model_dump()
                was_model = True

            if was_model and self.app.config["QUART_SCHEMA_CONVERT_CASING"]:
                query_string = camelize(query_string)

        return await super()._make_request(  # type: ignore
            path,
            method,
            headers,
            data,
            form,
            files,
            query_string,
            json,
            scheme,
            root_path,
            http_version,
            scope_base,
            auth,
            subdomain,
        )
