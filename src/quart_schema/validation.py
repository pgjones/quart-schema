from __future__ import annotations

from dataclasses import asdict, is_dataclass
from functools import wraps
from typing import Any, Callable, cast, Type, Union

from pydantic import BaseModel, ValidationError
from quart import request
from quart.exceptions import BadRequest
from werkzeug.datastructures import Headers

from .typing import BM, Dataclass, DC

QUART_SCHEMA_REQUEST_ATTRIBUTE = "_quart_schema_request_schema"
QUART_SCHEMA_RESPONSE_ATTRIBUTE = "_quart_schema_response_schemas"


class SchemaInvalidError(Exception):
    pass


class ResponseSchemaValidationError(Exception):
    pass


class RequestSchemaValidationError(BadRequest):
    pass


def validate_request(model_class: Union[Type[BaseModel], Type[Dataclass], None]) -> Callable:
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
