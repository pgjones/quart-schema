from __future__ import annotations

import sys
from dataclasses import fields, is_dataclass
from inspect import isclass
from typing import Any, Dict, List, Literal, Optional, Type, TypeVar, Union

import humps
from quart import current_app
from quart.typing import HeadersValue, ResponseReturnValue as QuartResponseReturnValue, StatusCode
from werkzeug.datastructures import Headers
from werkzeug.exceptions import HTTPException

from .typing import Model, PydanticDumpOptions, ResponseReturnValue, ResponseValue

if sys.version_info >= (3, 12):
    from typing import is_typeddict
else:
    from typing_extensions import is_typeddict

try:
    from pydantic import (
        BaseModel,
        RootModel,
        TypeAdapter,
        ValidationError as PydanticValidationError,
    )
    from pydantic.dataclasses import is_pydantic_dataclass
except ImportError:
    PYDANTIC_INSTALLED = False

    class BaseModel:  # type: ignore
        pass

    class RootModel:  # type: ignore
        pass

    class TypeAdapter:  # type: ignore
        pass

    def is_pydantic_dataclass(object_: Any) -> bool:  # type: ignore
        return False

    class PydanticValidationError(Exception):  # type: ignore
        pass

else:
    PYDANTIC_INSTALLED = True


try:
    from attrs import fields as attrs_fields, has as is_attrs
except ImportError:

    def is_attrs(object_: Any) -> bool:  # type: ignore
        return False


try:
    from msgspec import convert, Struct, to_builtins, ValidationError as MsgSpecValidationError
    from msgspec.json import schema_components
except ImportError:
    MSGSPEC_INSTALLED = False

    class Struct:  # type: ignore
        pass

    def convert(object_: Any, type_: Any) -> Any:  # type: ignore
        raise RuntimeError("Cannot convert, msgspec not installed")

    def to_builtins(object_: Any) -> Any:  # type: ignore
        return object_

    class MsgSpecValidationError(Exception):  # type: ignore
        pass

else:
    MSGSPEC_INSTALLED = True


PYDANTIC_REF_TEMPLATE = "#/components/schemas/{model}"
MSGSPEC_REF_TEMPLATE = "#/components/schemas/{name}"

T = TypeVar("T", bound=Model)

JsonSchemaMode = Literal["validation", "serialization"]


def convert_response_return_value(
    result: ResponseReturnValue | HTTPException,
) -> QuartResponseReturnValue | HTTPException:
    value: ResponseValue
    headers: Optional[HeadersValue] = None
    status: Optional[StatusCode] = None

    if isinstance(result, HTTPException):
        return result
    elif isinstance(result, tuple):
        if len(result) == 3:
            value, status, headers = result  # type: ignore
        elif len(result) == 2:
            value, status_or_headers = result
            if isinstance(status_or_headers, int):
                status = status_or_headers
            else:
                headers = status_or_headers  # type: ignore
    else:
        value = result

    value = model_dump(
        value,
        camelize=current_app.config["QUART_SCHEMA_CONVERT_CASING"],
        preference=current_app.config["QUART_SCHEMA_CONVERSION_PREFERENCE"],
        pydantic_kwargs=current_app.config["QUART_SCHEMA_PYDANTIC_DUMP_OPTIONS"],
    )
    headers = model_dump(
        headers,  # type: ignore
        kebabize=True,
        preference=current_app.config["QUART_SCHEMA_CONVERSION_PREFERENCE"],
        pydantic_kwargs=current_app.config["QUART_SCHEMA_PYDANTIC_DUMP_OPTIONS"],
    )

    new_result: ResponseReturnValue
    if isinstance(result, tuple):
        if len(result) == 3:
            new_result = value, status, headers
        elif len(result) == 2:
            if status is not None:
                new_result = value, status
            else:
                new_result = value, headers
    else:
        new_result = value

    return new_result


def model_dump(
    raw: ResponseValue,
    *,
    camelize: bool = False,
    kebabize: bool = False,
    preference: Optional[str] = None,
    pydantic_kwargs: Optional[PydanticDumpOptions] = None,
) -> dict | list:
    if is_pydantic_dataclass(type(raw)) or is_typeddict(type(raw)):
        value = RootModel[type(raw)](raw).model_dump(**(pydantic_kwargs or {}))  # type: ignore
    elif isinstance(raw, BaseModel):
        value = raw.model_dump(**(pydantic_kwargs or {}))
    elif isinstance(raw, Struct) or is_attrs(raw):  # type: ignore
        value = to_builtins(raw)
    elif (
        (isinstance(raw, (list, dict)) or is_dataclass(raw))
        and PYDANTIC_INSTALLED
        and preference != "msgspec"
    ):
        value = TypeAdapter(type(raw)).dump_python(raw, **(pydantic_kwargs or {}))
    elif (
        (isinstance(raw, (list, dict)) or is_dataclass(raw))
        and MSGSPEC_INSTALLED
        and preference != "pydantic"
    ):
        value = to_builtins(raw)
    else:
        return raw  # type: ignore

    if camelize:
        return humps.camelize(value)
    elif kebabize:
        return humps.kebabize(value)
    else:
        return value


def model_load(
    data: Union[dict, list],
    model_class: Type[T],
    exception_class: Type[Exception],
    *,
    decamelize: bool = False,
    preference: Optional[str] = None,
) -> T:
    if decamelize:
        data = humps.decamelize(data)

    try:
        if _use_pydantic(model_class, preference):
            return TypeAdapter(model_class).validate_python(data)
        elif _use_msgspec(model_class, preference):
            return convert(data, model_class, strict=False)
        elif not PYDANTIC_INSTALLED and not MSGSPEC_INSTALLED:
            raise RuntimeError(f"Cannot load {model_class} - try installing msgspec or pydantic")
        else:
            raise TypeError(f"Cannot load {model_class}")
    except (TypeError, MsgSpecValidationError, PydanticValidationError, ValueError) as error:
        raise exception_class(error)


def model_schema(
    model_class: Type[Model],
    *,
    preference: Optional[str] = None,
    schema_mode: JsonSchemaMode = "validation",
) -> dict:
    if _use_pydantic(model_class, preference):
        return TypeAdapter(model_class).json_schema(
            ref_template=PYDANTIC_REF_TEMPLATE, mode=schema_mode
        )
    elif _use_msgspec(model_class, preference):
        _, schema = schema_components([model_class], ref_template=MSGSPEC_REF_TEMPLATE)
        return list(schema.values())[0]
    elif not PYDANTIC_INSTALLED and not MSGSPEC_INSTALLED:
        raise TypeError(
            f"Cannot create schema for {model_class} - try installing msgspec or pydantic"
        )
    else:
        raise TypeError(f"Cannot create schema for {model_class}")


def convert_headers(
    raw: Union[Headers, dict], model_class: Type[T], exception_class: Type[Exception]
) -> T:
    if is_pydantic_dataclass(model_class):
        fields_ = set(model_class.__pydantic_fields__.keys())
    elif is_dataclass(model_class):
        fields_ = {field.name for field in fields(model_class)}
    elif is_typeddict(model_class):
        fields_ = {key for key in model_class.__annotations__.keys()}
    elif isclass(model_class) and issubclass(model_class, BaseModel):
        fields_ = set(model_class.model_fields.keys())
    elif isclass(model_class) and issubclass(model_class, Struct):
        fields_ = set(model_class.__struct_fields__)
    elif is_attrs(model_class):
        fields_ = {field.name for field in attrs_fields(model_class)}
    else:
        raise TypeError(f"Cannot convert to {model_class}")

    result = {}
    for raw_key in raw.keys():
        key = humps.dekebabize(raw_key).lower()
        if key in fields_:
            if isinstance(raw, Headers):
                result[key] = ",".join(raw.get_all(raw_key))
            else:
                result[key] = raw[raw_key]

    try:
        return model_class(**result)  # type: ignore[return-value]
    except (TypeError, MsgSpecValidationError, ValueError) as error:
        raise exception_class(error)


def _is_list_or_dict(type_: Type) -> bool:
    origin = getattr(type_, "__origin__", None)
    return origin in (dict, Dict, list, List)


def _use_pydantic(model_class: Type, preference: Optional[str]) -> bool:
    return PYDANTIC_INSTALLED and (
        is_pydantic_dataclass(model_class)
        or (isclass(model_class) and issubclass(model_class, BaseModel))
        or (
            (
                _is_list_or_dict(model_class)
                or is_dataclass(model_class)
                or is_typeddict(model_class)
            )
            and preference != "msgspec"
        )
    )


def _use_msgspec(model_class: Type, preference: Optional[str]) -> bool:
    return MSGSPEC_INSTALLED and (
        (isclass(model_class) and issubclass(model_class, Struct))
        or is_attrs(model_class)
        or (
            (
                _is_list_or_dict(model_class)
                or is_dataclass(model_class)
                or is_typeddict(model_class)
            )
            and preference != "pydantic"
        )
    )
