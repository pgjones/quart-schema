from typing import Callable, Optional
from quart import ResponseReturnValue as QuartResponseReturnValue
from .typing import Model
from .validation import QUART_SCHEMA_RESPONSE_ATTRIBUTE, _to_pydantic_model


def document_response(
    model_class: Model,
    status_code: int = 200,
    headers_model_class: Optional[Model] = None,
) -> Callable:
    """Document the response data.

    Add the response **model_class**, and its corresponding (optional)
    **headers_model_class** to the openapi generated documentation.

    Arguments:
        model_class: The model to use, either a dataclass, pydantic
            dataclass or a class that inherits from pydantic's
            BaseModel.
        status_code: The status code this validation applies
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
