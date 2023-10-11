from __future__ import annotations

from dataclasses import asdict, is_dataclass
from enum import auto, Enum
from functools import wraps
from typing import Any, Callable, cast, Dict, Optional, Tuple, Type, TypeVar, Union

from humps import decamelize
from pydantic import BaseModel, ValidationError
from pydantic.dataclasses import dataclass as pydantic_dataclass
from quart import current_app, request, Response, ResponseReturnValue as QuartResponseReturnValue
from werkzeug.datastructures import Headers
from werkzeug.exceptions import BadRequest
from werkzeug.wrappers import Response as WerkzeugResponse

from .typing import Model, PydanticModel, ResponseReturnValue

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
    FORM_MULTIPART = auto()
    JSON = auto()


def validate_querystring(model_class: Model) -> Callable:
    """Validate the request querystring arguments.

    This ensures that the query string arguments can be converted to
    the *model_class*. If they cannot a `RequestSchemaValidationError`
    is raised which by default results in a 400 response.

    Arguments:
        model_class: The model to use, either a dataclass, pydantic
            dataclass or a class that inherits from pydantic's
            BaseModel. All the fields must be optional.
    """
    model_class = _to_pydantic_model(model_class)

    def decorator(func: Callable) -> Callable:
        setattr(func, QUART_SCHEMA_QUERYSTRING_ATTRIBUTE, model_class)

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            request_args = {
                key: request.args.getlist(key)
                if len(request.args.getlist(key)) > 1
                else request.args[key]
                for key in request.args
            }
            if current_app.config["QUART_SCHEMA_CONVERT_CASING"]:
                request_args = decamelize(request_args)

            try:
                model = model_class(**request_args)
            except (TypeError, ValidationError) as error:
                raise QuerystringValidationError(error)
            else:
                return await current_app.ensure_async(func)(*args, query_args=model, **kwargs)

        return wrapper

    return decorator


def validate_headers(model_class: Model) -> Callable:
    """Validate the request headers.

    This ensures that the headers can be converted to the
    *model_class*. If they cannot a `RequestSchemaValidationError` is
    raised which by default results in a 400 response.

    Arguments:
        model_class: The model to use, either a dataclass, pydantic
            dataclass or a class that inherits from pydantic's
            BaseModel.

    """
    model_class = _to_pydantic_model(model_class)

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
    model_class: Model,
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
    model_class = _to_pydantic_model(model_class)

    def decorator(func: Callable) -> Callable:
        setattr(func, QUART_SCHEMA_REQUEST_ATTRIBUTE, (model_class, source))

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if source == DataSource.JSON:
                data = await request.get_json()
            else:
                data = (await request.form).to_dict()
                if source == DataSource.FORM_MULTIPART:
                    files = await request.files
                    for key in files:
                        if len(files.getlist(key)) > 1:
                            data[key] = files.getlist(key)
                        else:
                            data[key] = files[key]
            if current_app.config["QUART_SCHEMA_CONVERT_CASING"]:
                data = decamelize(data)
            try:
                model = model_class(**data)
            except (TypeError, ValidationError) as error:
                raise RequestSchemaValidationError(error)
            else:
                return await current_app.ensure_async(func)(*args, data=model, **kwargs)

        return wrapper

    return decorator


def validate_response(
    model_class: Model,
    status_code: int = 200,
    headers_model_class: Optional[Model] = None,
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
    model_class = _to_pydantic_model(model_class)
    headers_model_class = _to_pydantic_model(headers_model_class)

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
            elif isinstance(value, (Response, WerkzeugResponse)):
                status = value.status_code

            if isinstance(value, (Response, WerkzeugResponse)):
                if status == status_code:
                    raise ResponseHeadersValidationError()
                else:
                    return result

            if status == status_code:
                try:
                    if isinstance(value, dict):
                        model_value = model_class(**value)
                    elif type(value) == model_class:  # noqa: E721
                        model_value = value
                    elif is_dataclass(value):
                        model_value = model_class(**asdict(value))
                    else:
                        raise ResponseSchemaValidationError()
                except ValidationError as error:
                    raise ResponseSchemaValidationError(error)

                if headers_model_class is not None:
                    try:
                        if isinstance(headers, dict):
                            headers_model_value = _convert_headers(headers, headers_model_class)
                        elif type(headers) == headers_model_class:  # noqa: E721
                            headers_model_value = headers
                        elif is_dataclass(headers):
                            headers_model_value = headers_model_class(**asdict(headers))
                        else:
                            raise ResponseHeadersValidationError()
                    except ValidationError as error:
                        raise ResponseHeadersValidationError(error)

                    if is_dataclass(headers_model_value):
                        headers_value = asdict(headers_model_value)
                    else:
                        headers_value = cast(BaseModel, headers_model_value).model_dump()
                else:
                    headers_value = headers

                return model_value, status, headers_value
            else:
                return result

        return wrapper  # type: ignore

    return decorator


def validate(
    *,
    querystring: Optional[Model] = None,
    request: Optional[Model] = None,
    request_source: DataSource = DataSource.JSON,
    headers: Optional[Model] = None,
    responses: Dict[int, Tuple[Model, Optional[Model]]],
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


T = TypeVar("T")


def _convert_headers(headers: Union[dict, Headers], model_class: Type[T]) -> T:
    result = {}
    if is_dataclass(model_class):
        fields = model_class.__pydantic_fields__.keys()  # type: ignore
    else:
        fields = model_class.model_fields.keys()  # type: ignore
    for raw_key in headers.keys():
        key = raw_key.replace("-", "_").lower()
        if key in fields:
            if isinstance(headers, Headers):
                result[key] = ",".join(headers.get_all(raw_key))
            else:
                result[key] = headers[raw_key]
    return model_class(**result)


def _to_pydantic_model(model_class: Model) -> PydanticModel:
    pydantic_model_class: PydanticModel
    if is_dataclass(model_class):
        pydantic_model_class = pydantic_dataclass(model_class)
    else:
        pydantic_model_class = cast(PydanticModel, model_class)
    return pydantic_model_class
