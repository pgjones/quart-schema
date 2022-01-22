from __future__ import annotations

from dataclasses import asdict, is_dataclass
from enum import auto, Enum
from functools import wraps
from typing import Any, Callable, cast, Dict, Optional, Tuple, Type, TypeVar, Union

from pydantic import BaseModel, ValidationError
from pydantic.dataclasses import dataclass as pydantic_dataclass, is_builtin_dataclass
from pydantic.schema import model_schema
from quart import current_app, request, ResponseReturnValue as QuartResponseReturnValue
from werkzeug.datastructures import Headers
from werkzeug.exceptions import BadRequest

from .typing import PydanticModel, ResponseReturnValue

QUART_SCHEMA_HEADERS_ATTRIBUTE = "_quart_schema_headers_schema"
QUART_SCHEMA_REQUEST_ATTRIBUTE = "_quart_schema_request_schema"
QUART_SCHEMA_RESPONSE_ATTRIBUTE = "_quart_schema_response_schemas"
QUART_SCHEMA_QUERYSTRING_ATTRIBUTE = "_quart_schema_querystring_schema"


class SchemaInvalidError(Exception):
    pass


class ResponseSchemaValidationError(Exception):
    def __init__(self, validation_error: Optional[ValidationError] = None) -> None:
        self.validation_error = validation_error


class ResponseHeadersValidationError(ResponseSchemaValidationError):
    pass


class RequestSchemaValidationError(BadRequest):
    def __init__(self, validation_error: Union[TypeError, ValidationError]) -> None:
        super().__init__()
        self.validation_error = validation_error


class QuerystringValidationError(RequestSchemaValidationError):
    pass


class RequestHeadersValidationError(RequestSchemaValidationError):
    pass


class DataSource(Enum):
    FORM = auto()
    JSON = auto()


def validate_querystring(model_class: PydanticModel) -> Callable:
    """Validate the querystring arguments.

    This ensures that the query string arguments can be converted to
    the *model_class*. If they cannot a `RequestSchemaValidationError`
    is raised which by default results in a 400 response.

    Arguments:
        model_class: The model to use, either a dataclass, pydantic
            dataclass or a class that inherits from pydantic's
            BaseModel. All the fields must be optional.
    """
    if is_builtin_dataclass(model_class):
        model_class = pydantic_dataclass(model_class)

    schema = model_schema(model_class)

    if len(schema.get("required", [])) != 0:
        raise SchemaInvalidError("Fields must be optional")

    def decorator(func: Callable) -> Callable:
        setattr(func, QUART_SCHEMA_QUERYSTRING_ATTRIBUTE, model_class)

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                model = model_class(**request.args)
            except (TypeError, ValidationError) as error:
                raise QuerystringValidationError(error)
            else:
                return await current_app.ensure_async(func)(*args, query_args=model, **kwargs)

        return wrapper

    return decorator


def validate_headers(model_class: PydanticModel) -> Callable:
    """Validate the headers.

    This ensures that the headers can be converted to the
    *model_class*. If they cannot a `RequestSchemaValidationError` is
    raised which by default results in a 400 response.

    Arguments:
        model_class: The model to use, either a dataclass, pydantic
            dataclass or a class that inherits from pydantic's
            BaseModel.

    """
    if is_builtin_dataclass(model_class):
        model_class = pydantic_dataclass(model_class)

    def decorator(func: Callable) -> Callable:
        setattr(func, QUART_SCHEMA_HEADERS_ATTRIBUTE, model_class)

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                model = _convert_headers(request.headers, model_class)
            except (TypeError, ValidationError) as error:
                raise RequestHeadersValidationError(error)
            else:
                return await current_app.ensure_async(func)(*args, headers=model, **kwargs)

        return wrapper

    return decorator


def validate_request(
    model_class: PydanticModel,
    *,
    source: DataSource = DataSource.JSON,
) -> Callable:
    """Validate the request data.

    This ensures that the request body is JSON and that the body can
    be converted to the *model_class*. If they cannot a
    `RequestSchemaValidationError` is raised which by default results
    in a 400 response.

    Arguments:
        model_class: The model to use, either a dataclass, pydantic
            dataclass or a class that inherits from pydantic's
            BaseModel. All the fields must be optional.
        source: The source of the data to validate (json or form
            encoded).
    """
    if is_builtin_dataclass(model_class):
        model_class = pydantic_dataclass(model_class)

    schema = model_schema(model_class)
    if source == DataSource.FORM and any(
        schema["properties"][field]["type"] == "object" for field in schema["properties"]
    ):
        raise SchemaInvalidError("Form must not have nested objects")

    def decorator(func: Callable) -> Callable:
        setattr(func, QUART_SCHEMA_REQUEST_ATTRIBUTE, (model_class, source))

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if source == DataSource.JSON:
                data = await request.get_json()
            else:
                data = await request.form

            try:
                model = model_class(**data)
            except (TypeError, ValidationError) as error:
                raise RequestSchemaValidationError(error)
            else:
                return await current_app.ensure_async(func)(*args, data=model, **kwargs)

        return wrapper

    return decorator


def validate_response(
    model_class: PydanticModel,
    status_code: int = 200,
    headers_model_class: Optional[PydanticModel] = None,
) -> Callable:
    """Validate the response data.

    This ensures that the response is a either dictionary that the
    body can be converted to the *model_class* or an instance of the
    *model_class*. If this is not possible a
    `ResponseSchemaValidationError` is raised which by default results
    in a 500 response. The returned value is then a dictionary which
    Quart encodes as JSON.

    Arguments:
        model_class: The model to use, either a dataclass, pydantic
            dataclass or a class that inherits from pydantic's
            BaseModel.
        status_code: The status code this validation applies
            to. Defaults to 200.
         headers_model_class: The model to use to validate response
            headers, either a dataclass, pydantic dataclass or a class
            that inherits from pydantic's BaseModel. Is optional.
    """
    if is_builtin_dataclass(model_class):
        model_class = pydantic_dataclass(model_class)

    if is_builtin_dataclass(headers_model_class):
        headers_model_class = pydantic_dataclass(headers_model_class)

    def decorator(
        func: Callable[..., ResponseReturnValue]
    ) -> Callable[..., QuartResponseReturnValue]:
        schemas = getattr(func, QUART_SCHEMA_RESPONSE_ATTRIBUTE, {})
        schemas[status_code] = (model_class, headers_model_class)
        setattr(func, QUART_SCHEMA_RESPONSE_ATTRIBUTE, schemas)

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = await current_app.ensure_async(func)(*args, **kwargs)

            status_or_headers = None
            headers = None
            if isinstance(result, tuple):
                value, status_or_headers, headers = result + (None,) * (3 - len(result))
            else:
                value = result

            status = 200
            if isinstance(status_or_headers, int):
                status = int(status_or_headers)

            if status == status_code:
                try:
                    if isinstance(value, dict):
                        model_value = model_class(**value)
                    elif type(value) == model_class:
                        model_value = value
                    elif is_builtin_dataclass(value):
                        model_value = model_class(**asdict(value))
                    else:
                        raise ResponseSchemaValidationError()
                except ValidationError as error:
                    raise ResponseSchemaValidationError(error)

                if is_dataclass(model_value):
                    return_value = asdict(model_value)
                else:
                    return_value = cast(BaseModel, model_value).dict()

                if headers_model_class is not None:
                    try:
                        if isinstance(headers, dict):
                            headers_model_value = _convert_headers(headers, headers_model_class)
                        elif type(value) == headers_model_class:
                            headers_model_value = headers
                        elif is_builtin_dataclass(headers):
                            headers_model_value = headers_model_class(**asdict(headers))
                        else:
                            raise ResponseHeadersValidationError()
                    except ValidationError as error:
                        raise ResponseHeadersValidationError(error)

                    if is_dataclass(headers_model_value):
                        headers_value = asdict(headers_model_value)
                    else:
                        headers_value = cast(BaseModel, headers_model_value).dict()
                else:
                    headers_value = headers

                return return_value, status, headers_value
            else:
                return result

        return wrapper

    return decorator


def validate(
    *,
    querystring: Optional[PydanticModel] = None,
    request: Optional[PydanticModel] = None,
    request_source: DataSource = DataSource.JSON,
    headers: Optional[PydanticModel] = None,
    responses: Dict[int, Tuple[PydanticModel, Optional[PydanticModel]]],
) -> Callable:
    """Validate the route.

    This is a shorthand combination of of the validate_querystring,
    validate_request, validate_headers, and validate_response
    decorators. Please see the docstrings for those decorators.
    """

    def decorator(func: Callable) -> Callable:
        if querystring is not None:
            func = validate_querystring(querystring)(func)
        if request is not None:
            func = validate_request(request, source=request_source)(func)
        if headers is not None:
            func = validate_headers(headers)(func)
        for status, models in responses.items():
            func = validate_response(models[0], status, models[1])
        return func

    return decorator


T = TypeVar("T")


def _convert_headers(headers: Union[dict, Headers], model_class: Type[T]) -> T:
    result = {}
    for raw_key in headers.keys():
        key = raw_key.replace("-", "_").lower()
        if key in model_class.__annotations__:
            if isinstance(headers, Headers):
                result[key] = ",".join(headers.get_all(raw_key))
            else:
                result[key] = headers[raw_key]
    return model_class(**result)
