from typing import Any, Optional

import pytest
from hypothesis import given, strategies as st
from pydantic import BaseModel
from pydantic.dataclasses import dataclass
from quart import Quart

from quart_schema import DataSource, QuartSchema, validate_request


@dataclass
class DCDetails:
    name: str
    age: Optional[int] = None


class Details(BaseModel):
    name: str
    age: Optional[int]


@pytest.mark.asyncio
@pytest.mark.parametrize("type_", [DCDetails, Details])
async def test_send_json(type_: Any) -> None:
    app = Quart(__name__)
    QuartSchema(app)

    @app.route("/", methods=["POST"])
    @validate_request(type_)
    async def index(data: Any) -> Any:
        return data

    test_client = app.test_client()
    response = await test_client.post("/", json=type_(name="bob", age=2))
    assert (await response.get_json()) == {"name": "bob", "age": 2}


@pytest.mark.asyncio
@pytest.mark.parametrize("type_", [DCDetails, Details])
async def test_send_form(type_: Any) -> None:
    app = Quart(__name__)
    QuartSchema(app)

    @app.route("/", methods=["POST"])
    @validate_request(type_, source=DataSource.FORM)
    async def index(data: Any) -> Any:
        return data

    test_client = app.test_client()
    response = await test_client.post("/", form=type_(name="bob", age=2))
    assert (await response.get_json()) == {"name": "bob", "age": 2}


@given(st.builds(DCDetails))
@pytest.mark.asyncio
async def test_hypothesis_dataclass(data: DCDetails) -> None:
    app = Quart(__name__)
    QuartSchema(app)

    @app.route("/", methods=["POST"])
    @validate_request(DCDetails)  # type: ignore
    async def index(data: DCDetails) -> Any:
        return data

    test_client = app.test_client()
    response = await test_client.post("/", json=data)
    assert response.status_code == 200
