from __future__ import annotations

from typing import Any, AnyStr, Dict, Optional, Tuple, Type, Union

from quart import current_app, Response
from quart.datastructures import FileStorage
from quart.testing.utils import sentinel
from werkzeug.datastructures import Authorization, Headers

from .conversion import model_dump, model_load
from .typing import Model, TestClientProtocol, WebsocketProtocol


class SchemaValidationError(Exception):
    def __init__(self, validation_error: Optional[Exception] = None) -> None:
        super().__init__()
        self.validation_error = validation_error


class WebsocketMixin:
    async def receive_as(self: WebsocketProtocol, model_class: Type[Model]) -> Model:
        data = await self.receive_json()
        return model_load(
            data,
            model_class,
            SchemaValidationError,
            decamelize=current_app.config["QUART_SCHEMA_CONVERT_CASING"],
            preference=current_app.config["QUART_SCHEMA_CONVERSION_PREFERENCE"],
        )

    async def send_as(self: WebsocketProtocol, value: Any, model_class: Type[Model]) -> None:
        if type(value) != model_class:  # noqa: E721
            value = model_load(
                value,
                model_class,
                SchemaValidationError,
                preference=current_app.config["QUART_SCHEMA_CONVERSION_PREFERENCE"],
            )
        data = model_dump(
            value,
            camelize=current_app.config["QUART_SCHEMA_CONVERT_CASING"],
            preference=current_app.config["QUART_SCHEMA_CONVERSION_PREFERENCE"],
            pydantic_kwargs=current_app.config["QUART_SCHEMA_PYDANTIC_DUMP_OPTIONS"],
        )
        await self.send_json(data)  # type: ignore


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
            json = model_dump(
                json,
                camelize=self.app.config["QUART_SCHEMA_CONVERT_CASING"],
                preference=self.app.config["QUART_SCHEMA_CONVERSION_PREFERENCE"],
                pydantic_kwargs=self.app.config["QUART_SCHEMA_PYDANTIC_DUMP_OPTIONS"],
            )

        if form is not None:
            form = model_dump(  # type: ignore
                form,
                camelize=self.app.config["QUART_SCHEMA_CONVERT_CASING"],
                preference=self.app.config["QUART_SCHEMA_CONVERSION_PREFERENCE"],
                pydantic_kwargs=self.app.config["QUART_SCHEMA_PYDANTIC_DUMP_OPTIONS"],
            )
        if query_string is not None:
            query_string = model_dump(  # type: ignore
                query_string,
                camelize=self.app.config["QUART_SCHEMA_CONVERT_CASING"],
                preference=self.app.config["QUART_SCHEMA_CONVERSION_PREFERENCE"],
                pydantic_kwargs=self.app.config["QUART_SCHEMA_PYDANTIC_DUMP_OPTIONS"],
            )

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
