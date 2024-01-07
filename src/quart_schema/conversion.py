from __future__ import annotations

from dataclasses import asdict, fields, is_dataclass
from typing import Optional, Type, TypeVar, Union

import humps
from pydantic import BaseModel, RootModel, ValidationError
from pydantic.dataclasses import dataclass as pydantic_dataclass, is_pydantic_dataclass
from pydantic.json_schema import GenerateJsonSchema
from quart import current_app
from quart.typing import HeadersValue, ResponseReturnValue as QuartResponseReturnValue, StatusCode
from werkzeug.datastructures import Headers

from .typing import BM, DC, Model, ResponseReturnValue, ResponseValue

REF_TEMPLATE = "#/components/schemas/{model}"

T = TypeVar("T")


def convert_response_return_value(result: ResponseReturnValue) -> QuartResponseReturnValue:
    value: ResponseValue
    headers: Optional[HeadersValue] = None
    status: Optional[StatusCode] = None

    if isinstance(result, tuple):
        if len(result) == 3:
            value, status, headers = result  # type: ignore
        elif len(result) == 2:
            value, status_or_headers = result
            if isinstance(status_or_headers, int):
                status = status_or_headers
    else:
        value = result

    value = model_dump(
        value,
        camelize=current_app.config["QUART_SCHEMA_CONVERT_CASING"],
        by_alias=current_app.config["QUART_SCHEMA_BY_ALIAS"],
    )
    headers = model_dump(
        headers,  # type: ignore
        kebabize=True,
        by_alias=current_app.config["QUART_SCHEMA_BY_ALIAS"],
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
    raw: ResponseValue, *, by_alias: bool, camelize: bool = False, kebabize: bool = False
) -> dict:
    if is_pydantic_dataclass(raw):  # type: ignore
        value = RootModel[type(raw)](raw).model_dump()  # type: ignore
    elif is_dataclass(raw):
        value = asdict(raw)  # type: ignore
    elif isinstance(raw, BaseModel):
        value = raw.model_dump(by_alias=by_alias)
    else:
        return raw  # type: ignore

    if camelize:
        return humps.camelize(value)
    elif kebabize:
        return humps.kebabize(value)
    else:
        return value


def model_load(
    data: dict, model_class: Model, exception_class: Type[Exception], *, decamelize: bool = False
) -> Union[BM, DC]:
    if decamelize:
        data = humps.decamelize(data)
    try:
        return model_class(**data)  # type: ignore
    except (TypeError, ValidationError, ValueError) as error:
        raise exception_class(error)


def model_schema(model_class: Model) -> dict:
    if is_pydantic_dataclass(model_class):
        return GenerateJsonSchema(ref_template=REF_TEMPLATE).generate(
            model_class.__pydantic_core_schema__
        )
    elif is_dataclass(model_class):
        pydantic_model_class = pydantic_dataclass(model_class)
        return GenerateJsonSchema(ref_template=REF_TEMPLATE).generate(
            pydantic_model_class.__pydantic_core_schema__
        )
    elif issubclass(model_class, BaseModel):
        return model_class.model_json_schema(ref_template=REF_TEMPLATE)
    else:
        raise TypeError(f"Cannot produce schema for {model_class}")


def convert_headers(
    raw: Union[Headers, dict], model_class: Type[T], exception_class: Type[Exception]
) -> T:
    if is_pydantic_dataclass(model_class):
        fields_ = model_class.__pydantic_fields__.keys()
    elif is_dataclass(model_class):
        fields_ = {field.name for field in fields(model_class)}  # type: ignore
    elif issubclass(model_class, BaseModel):
        fields_ = model_class.model_fields.keys()
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
        return model_class(**result)
    except (TypeError, ValidationError, ValueError) as error:
        raise exception_class(error)
