from typing import Any, Callable
from quart import request, jsonify
from functools import wraps
from pydantic import GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from quart.datastructures import FileStorage





# Create a decorator function for Pydantic Base model validation
#Able to take in base model and all that's needed is the class
#This is all without any changes to normal pydantice model
def validate_pydantic_model(model, error_msg="", error_code=400):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Parse and validate the request JSON using the provided Pydantic model
                data = model(** await request.get_json())
                return func(data, *args, **kwargs)
            except Exception as e:
                return jsonify({'error': e if error_msg == "" else error_msg}), error_code
        return wrapper
    return decorator

try:
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated  # type: ignore


class _File:
    @classmethod
    def _validate(cls, value: Any, _: Any) -> FileStorage:  # noqa: N805
        if not isinstance(value, FileStorage):
            raise ValueError(f"Expected FileStorage, received: {type(value)}")
        return value

    @classmethod
    def __get_pydantic_core_schema__(
        cls,  # noqa: N805
        _source_type: Any,
        _handler: Callable[[Any], core_schema.CoreSchema],
    ) -> core_schema.CoreSchema:
        return core_schema.general_plain_validator_function(cls._validate)

    @classmethod
    def __get_pydantic_json_schema__(
        cls,  # noqa: N805
        core_schema: core_schema.CoreSchema,
        handler: GetJsonSchemaHandler,
    ) -> JsonSchemaValue:
        return {"type": "string", "format": "binary"}


File = Annotated[FileStorage, _File]
