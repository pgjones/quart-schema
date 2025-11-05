from __future__ import annotations

from typing import Any, AnyStr

from quart import current_app, Response
from quart.datastructures import FileStorage
from quart.testing.utils import sentinel
from werkzeug.datastructures import Authorization, Headers

from .conversion import model_dump, model_load
from .typing import Model, TestClientProtocol, WebsocketProtocol


class SchemaValidationError(Exception):
    def __init__(self, validation_error: Exception | None = None) -> None:
        super().__init__()
        self.validation_error = validation_error


class WebsocketMixin:
    async def receive_as(self: WebsocketProtocol, model_class: type[Model]) -> Model:
        data = await self.receive_json()
        return model_load(
            data,
            model_class,
            SchemaValidationError,
            decamelize=current_app.config["QUART_SCHEMA_CONVERT_CASING"],
            preference=current_app.config["QUART_SCHEMA_CONVERSION_PREFERENCE"],
        )

    async def send_as(self: WebsocketProtocol, value: Any, model_class: type[Model]) -> None:
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
        headers: dict | Headers | None,
        data: AnyStr | None,
        form: dict | None,
        files: dict[str, FileStorage] | None,
        query_string: dict | None,
        json: Any,
        scheme: str,
        root_path: str,
        http_version: str,
        scope_base: dict | None,
        auth: Authorization | tuple[str, str] | None = None,
        subdomain: str | None = None,
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
