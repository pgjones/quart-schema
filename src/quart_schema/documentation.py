from typing import Callable, Dict, Optional, Tuple

from quart import ResponseReturnValue as QuartResponseReturnValue

from .typing import Model
from .validation import (
    _to_pydantic_model,
    DataSource,
    QUART_SCHEMA_HEADERS_ATTRIBUTE,
    QUART_SCHEMA_QUERYSTRING_ATTRIBUTE,
    QUART_SCHEMA_REQUEST_ATTRIBUTE,
    QUART_SCHEMA_RESPONSE_ATTRIBUTE,
)


def document_querystring(model_class: Model) -> Callable:
    """Document the request querystring arguments.

    Add the request querystring **model_class** to the openapi
    generated documentation for the request querystring.

    Arguments:
        model_class: The model to use, either a dataclass, pydantic
            dataclass or a class that inherits from pydantic's
            BaseModel. All the fields must be optional.

    """
    model_class = _to_pydantic_model(model_class)

    def decorator(func: Callable) -> Callable:
        setattr(func, QUART_SCHEMA_QUERYSTRING_ATTRIBUTE, model_class)

        return func

    return decorator


def document_headers(model_class: Model) -> Callable:
    """Document the request headers.

    Add the request **model_class** to the openapi generated
    documentation for the request headers.

    Arguments:
        model_class: The model to use, either a dataclass, pydantic
            dataclass or a class that inherits from pydantic's
            BaseModel.

    """
    model_class = _to_pydantic_model(model_class)

    def decorator(func: Callable) -> Callable:
        setattr(func, QUART_SCHEMA_HEADERS_ATTRIBUTE, model_class)

        return func

    return decorator


def document_request(
    model_class: Model,
    *,
    source: DataSource = DataSource.JSON,
) -> Callable:
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
    model_class = _to_pydantic_model(model_class)

    def decorator(func: Callable) -> Callable:
        setattr(func, QUART_SCHEMA_REQUEST_ATTRIBUTE, (model_class, source))

        return func

    return decorator


def document_response(
    model_class: Model,
    status_code: int = 200,
    headers_model_class: Optional[Model] = None,
) -> Callable:
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
    model_class = _to_pydantic_model(model_class)
    headers_model_class = _to_pydantic_model(headers_model_class)

    def decorator(
        func: Callable[..., QuartResponseReturnValue]
    ) -> Callable[..., QuartResponseReturnValue]:
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
) -> Callable:
    """Document the route.

    This is a shorthand combination of of the document_querystring,
    document_request, document_headers, and document_response
    decorators. Please see the docstrings for those decorators.
    """

    def decorator(func: Callable) -> Callable:
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
