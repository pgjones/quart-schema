from typing import Callable, Dict, Optional, Tuple, TypeVar

from .typing import Model
from .validation import (
    DataSource,
    QUART_SCHEMA_HEADERS_ATTRIBUTE,
    QUART_SCHEMA_QUERYSTRING_ATTRIBUTE,
    QUART_SCHEMA_REQUEST_ATTRIBUTE,
    QUART_SCHEMA_RESPONSE_ATTRIBUTE,
)

T = TypeVar("T", bound=Callable)


def document_querystring(model_class: Model) -> Callable[[T], T]:
    """Document the request querystring arguments.

    Add the request querystring **model_class** to the openapi
    generated documentation for the request querystring.

    Arguments:
        model_class: The model to use, either a dataclass, pydantic
            dataclass or a class that inherits from pydantic's
            BaseModel. All the fields must be optional.

    """

    def decorator(func: T) -> T:
        setattr(func, QUART_SCHEMA_QUERYSTRING_ATTRIBUTE, model_class)

        return func

    return decorator


def document_headers(model_class: Model) -> Callable[[T], T]:
    """Document the request headers.

    Add the request **model_class** to the openapi generated
    documentation for the request headers.

    Arguments:
        model_class: The model to use, either a dataclass, pydantic
            dataclass or a class that inherits from pydantic's
            BaseModel.

    """

    def decorator(func: T) -> T:
        setattr(func, QUART_SCHEMA_HEADERS_ATTRIBUTE, model_class)

        return func

    return decorator


def document_request(
    model_class: Model,
    *,
    source: DataSource = DataSource.JSON,
) -> Callable[[T], T]:
    """Document the request data.

    Add the request **model_class** to the openapi generated
    documentation for the request body.

    Arguments:
        model_class: The model to use, either a dataclass, pydantic
            dataclass or a class that inherits from pydantic's
            BaseModel.
        source: The source of the data to validate (json or form
            encoded).
    """

    def decorator(func: T) -> T:
        setattr(func, QUART_SCHEMA_REQUEST_ATTRIBUTE, (model_class, source))

        return func

    return decorator


def document_response(
    model_class: Model,
    status_code: int = 200,
    headers_model_class: Optional[Model] = None,
) -> Callable[[T], T]:
    """Document the response data.

    Add the response **model_class**, and its corresponding (optional)
    **headers_model_class** to the openapi generated documentation for
    the response body.

    Arguments:
        model_class: The model to use, either a dataclass, pydantic
            dataclass or a class that inherits from pydantic's
            BaseModel.
        status_code: The status code this documentation applies
            to. Defaults to 200.
        headers_model_class: The model to use to document the response
            headers, either a dataclass, pydantic dataclass or a class
            that inherits from pydantic's BaseModel. Is optional.

    """

    def decorator(func: T) -> T:
        schemas = getattr(func, QUART_SCHEMA_RESPONSE_ATTRIBUTE, {})
        schemas[status_code] = (model_class, headers_model_class)
        setattr(func, QUART_SCHEMA_RESPONSE_ATTRIBUTE, schemas)

        return func

    return decorator


def document(
    *,
    querystring: Optional[Model] = None,
    request: Optional[Model] = None,
    request_source: DataSource = DataSource.JSON,
    headers: Optional[Model] = None,
    responses: Dict[int, Tuple[Model, Optional[Model]]],
) -> Callable[[T], T]:
    """Document the route.

    This is a shorthand combination of of the document_querystring,
    document_request, document_headers, and document_response
    decorators. Please see the docstrings for those decorators.
    """

    def decorator(func: T) -> T:
        if querystring is not None:
            func = document_querystring(querystring)(func)
        if request is not None:
            func = document_request(request, source=request_source)(func)
        if headers is not None:
            func = document_headers(headers)(func)
        for status, models in responses.items():
            func = document_response(models[0], status, models[1])(func)
        return func

    return decorator
