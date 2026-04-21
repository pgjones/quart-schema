from dataclasses import dataclass
from typing import Any, TypedDict

import pytest
from attrs import define
from msgspec import Struct
from pydantic import BaseModel
from pydantic.dataclasses import dataclass as pydantic_dataclass

from quart_schema.conversion import convert_headers, model_dump, model_load, model_schema
from .helpers import ADetails, DCDetails, MDetails, PyDCDetails, PyDetails, TDetails, TGDetails


class ValidationError(Exception):
    pass


@pytest.mark.parametrize(
    "type_",
    [ADetails, DCDetails, MDetails, PyDetails, PyDCDetails, TDetails, TGDetails],
)
def test_model_dump(
    type_: type[ADetails | DCDetails | MDetails | PyDetails | PyDCDetails | TGDetails],
) -> None:
    assert model_dump(type_(name="bob", age=2)) == {
        "name": "bob",
        "age": 2,
    }


test_types_and_preference = [
    (ADetails, "msgspec"),
    (DCDetails, "msgspec"),
    (DCDetails, "pydantic"),
    (MDetails, "msgspec"),
    (TGDetails, "msgspec"),
    (TGDetails, "pydantic"),
    (PyDetails, "pydantic"),
    (PyDCDetails, "pydantic"),
    (TDetails, "pydantic"),
]
test_types = [
    ADetails,
    DCDetails,
    MDetails,
    PyDetails,
    PyDCDetails,
    TDetails,
    TGDetails,
]

TestType = type[ADetails | DCDetails | MDetails | PyDetails | PyDCDetails | TDetails]


@pytest.mark.parametrize("type_, preference", test_types_and_preference)
def test_model_dump_list(type_: TestType, preference: str) -> None:
    assert model_dump(
        [type_(name="bob", age=2), type_(name="jim", age=3)],
        preference=preference,
    ) == [{"name": "bob", "age": 2}, {"name": "jim", "age": 3}]


@pytest.mark.parametrize("type_, preference", test_types_and_preference)
def test_model_load(type_: TestType, preference: str) -> None:
    assert model_load(
        {"name": "bob", "age": 2},
        type_,
        exception_class=ValidationError,
        preference=preference,
    ) == type_(name="bob", age=2)


@pytest.mark.parametrize("type_, preference", test_types_and_preference)
def test_model_load_list(type_: TestType, preference: str) -> None:
    assert model_load(
        [{"name": "bob", "age": 2}],
        list[type_],  # type: ignore
        exception_class=ValidationError,
        preference=preference,
    ) == [type_(name="bob", age=2)]


@pytest.mark.parametrize("type_, preference", test_types_and_preference)
def test_model_load_error(type_: TestType, preference: str) -> None:
    with pytest.raises(ValidationError):
        model_load(
            {"name": "bob", "age": "two"},
            type_,
            exception_class=ValidationError,
            preference=preference,
        )


@pytest.mark.parametrize("type_, preference", test_types_and_preference)
def test_model_schema_msgspec(type_: TestType, preference: str) -> None:
    schema = model_schema(
        type_,
        preference=preference,
    )

    # Base expected schema (common to both)
    expected: dict[str, Any] = {
        "title": type_.__name__,
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {
                "anyOf": [
                    {"type": "integer"},
                    {"type": "null"},
                ],
                "default": None,
            },
        },
        "required": ["name"],
    }

    # Pydantic adds "title" fields to properties
    if preference == "pydantic":
        expected["properties"]["name"]["title"] = "Name"
        expected["properties"]["age"]["title"] = "Age"

    # For some reason the name for aliased type dicts
    # includes the generic in msgspec
    if preference == "msgspec" and type_ is TGDetails:
        expected["title"] = "_TGDetails[str]"

    # TGDetails does not include the default for age
    if type_ is TGDetails:
        del expected["properties"]["age"]["default"]

    assert schema == expected


@define
class AHeaders:
    x_info: str


class MHeaders(Struct):
    x_info: str


@dataclass
class DCHeaders:
    x_info: str


class PyHeaders(BaseModel):
    x_info: str


@pydantic_dataclass
class PyDCHeaders:
    x_info: str


class THeaders(TypedDict):
    x_info: str


@pytest.mark.parametrize("type_", [AHeaders, DCHeaders, MHeaders, PyHeaders, PyDCHeaders, THeaders])
def test_convert_headers(
    type_: type[AHeaders | DCHeaders | MHeaders | PyHeaders | PyDCHeaders | THeaders],
) -> None:
    convert_headers(
        {
            "X-Info": "ABC",
            "Other": "2",
        },
        type_,
        exception_class=ValidationError,
    ) == type_(x_info="ABC")
