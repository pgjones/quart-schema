from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, AnyStr, cast, Optional, overload, Type, Union

from pydantic import BaseModel, ValidationError
from quart import Response
from quart.testing.utils import sentinel
from werkzeug.datastructures import Headers

from .typing import BM, DC, TestClientProtocol, WebsocketProtocol


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


class TestClientMixin:
    async def _make_request(
        self: TestClientProtocol,
        path: str,
        method: str,
        headers: Optional[Union[dict, Headers]],
        data: Optional[AnyStr],
        form: Any,
        query_string: Any,
        json: Any,
        scheme: str,
        root_path: str,
        http_version: str,
    ) -> Response:
        if json is not sentinel:
            if is_dataclass(json):
                json = asdict(json)
            elif isinstance(json, BaseModel):
                json = json.dict()
        if form is not None:
            if is_dataclass(form):
                form = asdict(form)
            elif isinstance(form, BaseModel):
                form = form.dict()
        if query_string is not None:
            if is_dataclass(query_string):
                query_string = asdict(query_string)
            elif isinstance(query_string, BaseModel):
                query_string = query_string.dict()
        return await super()._make_request(  # type: ignore
            path, method, headers, data, form, query_string, json, scheme, root_path, http_version
        )
