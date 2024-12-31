from typing import Annotated, Any, Callable

from pydantic import GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from quart.datastructures import FileStorage


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
        return core_schema.with_info_plain_validator_function(cls._validate)

    @classmethod
    def __get_pydantic_json_schema__(
        cls,  # noqa: N805
        core_schema: core_schema.CoreSchema,
        handler: GetJsonSchemaHandler,
    ) -> JsonSchemaValue:
        return {"type": "string", "format": "binary"}


File = Annotated[FileStorage, _File]
