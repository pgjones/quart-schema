from __future__ import annotations

from collections.abc import Callable
from enum import auto, Enum
from functools import lru_cache, wraps
from types import UnionType
from typing import Any, get_args, get_origin, get_type_hints, Union

from quart import current_app, request, Response
from werkzeug.exceptions import BadRequest
from werkzeug.wrappers import Response as WerkzeugResponse

from .casing import camel_to_snake
from .conversion import convert_headers, model_load
from .typing import Model, ResponseReturnValue

QUART_SCHEMA_HEADERS_ATTRIBUTE = "_quart_schema_headers_schema"
QUART_SCHEMA_REQUEST_ATTRIBUTE = "_quart_schema_request_schema"
QUART_SCHEMA_RESPONSE_ATTRIBUTE = "_quart_schema_response_schemas"
QUART_SCHEMA_QUERYSTRING_ATTRIBUTE = "_quart_schema_querystring_schema"


class SchemaInvalidError(Exception):
    pass


class ResponseSchemaValidationError(Exception):
    def __init__(self, validation_error: Exception | None = None) -> None:
        self.validation_error = validation_error


class ResponseHeadersValidationError(ResponseSchemaValidationError):
    pass


class RequestSchemaValidationError(BadRequest):
    def __init__(self, validation_error: Exception) -> None:
        super().__init__()
        self.validation_error = validation_error


class QuerystringValidationError(RequestSchemaValidationError):
    pass


class RequestHeadersValidationError(RequestSchemaValidationError):
    pass


class DataSource(Enum):
    FORM = auto()
    FORM_MULTIPART = auto()
    JSON = auto()


_LIST_CONTAINERS: tuple[type, ...] = (list, tuple, set, frozenset)


@lru_cache(maxsize=128)
def _list_field_names(model_class: type[Model]) -> frozenset[str]:
    """Return the names of fields in *model_class* that expect list values.

    Handles ``Optional``/``Union`` wrappers (e.g. ``list[int] | None``) and
    caches results per model class for repeated calls.

    Falls back to raw ``__annotations__`` if forward references cannot be
    resolved.
    """

    def _expects_list(annotation: Any) -> bool:
        origin = get_origin(annotation)
        if origin in (Union, UnionType):
            return any(_expects_list(arg) for arg in get_args(annotation))
        if origin is not None:
            return origin in _LIST_CONTAINERS
        return annotation in _LIST_CONTAINERS

    try:
        hints = get_type_hints(model_class)
    except (NameError, TypeError):
        hints = getattr(model_class, "__annotations__", {})

    return frozenset(name for name, annotation in hints.items() if _expects_list(annotation))


def validate_querystring(model_class: type[Model]) -> Callable:
    """Validate the request querystring arguments.

    This ensures that the query string arguments can be converted to
    the *model_class*. If they cannot a `RequestSchemaValidationError`
    is raised which by default results in a 400 response.

    Arguments:
        model_class: The model to use, either a dataclass, pydantic
            dataclass or a class that inherits from pydantic's
            BaseModel. All the fields must be optional.
    """
    # mypy can't prove type[Model] is hashable and lru_cache requires hashable arguments
    list_fields = _list_field_names(model_class)  # type: ignore[arg-type]

    def decorator(func: Callable) -> Callable:
        setattr(func, QUART_SCHEMA_QUERYSTRING_ATTRIBUTE, model_class)

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            request_args: dict[str, Any] = {}
            decamelize = current_app.config["QUART_SCHEMA_CONVERT_CASING"]

            for key in request.args:
                # Strip [] suffix for array syntax
                clean_key = key.removesuffix("[]") if key.endswith("[]") else key
                # Apply casing conversion for model matching
                model_key = camel_to_snake(clean_key) if decamelize else clean_key
                values = request.args.getlist(key)

                # List fields always get lists; scalars get single values
                if len(values) > 1 or model_key in list_fields:
                    request_args[model_key] = values
                else:
                    request_args[model_key] = values[0] if values else None

            model = model_load(
                request_args,
                model_class,
                QuerystringValidationError,
                decamelize=decamelize,
                preference=current_app.config["QUART_SCHEMA_CONVERSION_PREFERENCE"],
            )
            return await current_app.ensure_async(func)(*args, query_args=model, **kwargs)

        return wrapper

    return decorator


def validate_headers(model_class: type[Model]) -> Callable:
    """Validate the request headers.

    This ensures that the headers can be converted to the
    *model_class*. If they cannot a `RequestSchemaValidationError` is
    raised which by default results in a 400 response.

    Arguments:
        model_class: The model to use, either a dataclass, pydantic
            dataclass or a class that inherits from pydantic's
            BaseModel.

    """

    def decorator(func: Callable) -> Callable:
        setattr(func, QUART_SCHEMA_HEADERS_ATTRIBUTE, model_class)

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            model = convert_headers(request.headers, model_class, RequestHeadersValidationError)
            return await current_app.ensure_async(func)(*args, headers=model, **kwargs)

        return wrapper

    return decorator


def validate_request(
    model_class: type[Model],
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
            BaseModel.
        source: The source of the data to validate (json or form
            encoded).
    """

    def decorator(func: Callable) -> Callable:
        setattr(func, QUART_SCHEMA_REQUEST_ATTRIBUTE, (model_class, source))

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if source == DataSource.JSON:
                data = await request.get_json()
            else:
                data = {}
                form = await request.form
                for key in form:
                    if len(form.getlist(key)) > 1:
                        data[key] = form.getlist(key)
                    else:
                        data[key] = form[key]
                if source == DataSource.FORM_MULTIPART:
                    files = await request.files
                    for key in files:
                        if len(files.getlist(key)) > 1:
                            data[key] = files.getlist(key)
                        else:
                            data[key] = files[key]

            model = model_load(
                data,
                model_class,
                RequestSchemaValidationError,
                decamelize=current_app.config["QUART_SCHEMA_CONVERT_CASING"],
                preference=current_app.config["QUART_SCHEMA_CONVERSION_PREFERENCE"],
            )
            return await current_app.ensure_async(func)(*args, data=model, **kwargs)

        return wrapper

    return decorator


def validate_response(
    model_class: type[Model],
    status_code: int = 200,
    headers_model_class: type[Model] | None = None,
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

    def decorator(func: Callable[..., ResponseReturnValue]) -> Callable[..., ResponseReturnValue]:
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
            elif isinstance(value, (Response, WerkzeugResponse)):
                status = value.status_code

            if isinstance(value, (Response, WerkzeugResponse)):
                if status == status_code:
                    raise RuntimeError("Cannot validate Response instance")
                else:
                    return result

            if status == status_code:
                if type(value) == model_class:  # noqa: E721
                    model_value = value
                else:
                    model_value = model_load(
                        value,  # type: ignore
                        model_class,
                        ResponseSchemaValidationError,
                        preference=current_app.config["QUART_SCHEMA_CONVERSION_PREFERENCE"],
                    )

                if headers_model_class is not None:
                    if type(headers) == headers_model_class:  # noqa: E721
                        headers_value = headers
                    else:
                        headers_value = convert_headers(
                            headers,  # type: ignore
                            headers_model_class,
                            ResponseHeadersValidationError,
                        )
                else:
                    headers_value = headers

                return model_value, status, headers_value
            else:
                return result

        return wrapper  # type: ignore

    return decorator


def validate(
    *,
    querystring: type[Model] | None = None,
    request: type[Model] | None = None,
    request_source: DataSource = DataSource.JSON,
    headers: type[Model] | None = None,
    responses: dict[int, tuple[type[Model], type[Model] | None]],
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
            func = validate_response(models[0], status, models[1])(func)
        return func

    return decorator
