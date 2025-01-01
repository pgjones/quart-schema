from __future__ import annotations

from enum import auto, Enum
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple, Type

from quart import current_app, request, Response
from werkzeug.exceptions import BadRequest
from werkzeug.wrappers import Response as WerkzeugResponse

from .conversion import convert_headers, model_load
from .typing import Model, ResponseReturnValue

QUART_SCHEMA_HEADERS_ATTRIBUTE = "_quart_schema_headers_schema"
QUART_SCHEMA_REQUEST_ATTRIBUTE = "_quart_schema_request_schema"
QUART_SCHEMA_RESPONSE_ATTRIBUTE = "_quart_schema_response_schemas"
QUART_SCHEMA_QUERYSTRING_ATTRIBUTE = "_quart_schema_querystring_schema"


class SchemaInvalidError(Exception):
    pass


class ResponseSchemaValidationError(Exception):
    def __init__(self, validation_error: Optional[Exception] = None) -> None:
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


def validate_querystring(model_class: Type[Model]) -> Callable:
    """Validate the request querystring arguments.

    This ensures that the query string arguments can be converted to
    the *model_class*. If they cannot a `RequestSchemaValidationError`
    is raised which by default results in a 400 response.

    Arguments:
        model_class: The model to use, either a dataclass, pydantic
            dataclass or a class that inherits from pydantic's
            BaseModel. All the fields must be optional.
    """

    def decorator(func: Callable) -> Callable:
        setattr(func, QUART_SCHEMA_QUERYSTRING_ATTRIBUTE, model_class)

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            request_args = {
                key: (
                    request.args.getlist(key)
                    if len(request.args.getlist(key)) > 1
                    else request.args[key]
                )
                for key in request.args
            }
            model = model_load(
                request_args,
                model_class,
                QuerystringValidationError,
                decamelize=current_app.config["QUART_SCHEMA_CONVERT_CASING"],
                preference=current_app.config["QUART_SCHEMA_CONVERSION_PREFERENCE"],
            )
            return await current_app.ensure_async(func)(*args, query_args=model, **kwargs)

        return wrapper

    return decorator


def validate_headers(model_class: Type[Model]) -> Callable:
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
    model_class: Type[Model],
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
    model_class: Type[Model],
    status_code: int = 200,
    headers_model_class: Optional[Type[Model]] = None,
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
    querystring: Optional[Type[Model]] = None,
    request: Optional[Type[Model]] = None,
    request_source: DataSource = DataSource.JSON,
    headers: Optional[Type[Model]] = None,
    responses: Dict[int, Tuple[Type[Model], Optional[Type[Model]]]],
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
