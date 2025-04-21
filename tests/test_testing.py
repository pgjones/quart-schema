from typing import Type, Union

import pytest
from hypothesis import given, strategies as st
from quart import Quart

from quart_schema import DataSource, QuartSchema, validate_request
from .helpers import ADetails, DCDetails, MDetails, PyDCDetails, PyDetails, TDetails

Models = Union[ADetails, DCDetails, MDetails, PyDetails, PyDCDetails, TDetails]


@pytest.mark.parametrize("type_", [ADetails, DCDetails, MDetails, PyDetails, PyDCDetails, TDetails])
async def test_send_json(type_: Type[Models]) -> None:
    app = Quart(__name__)
    QuartSchema(app)

    @app.route("/", methods=["POST"])
    @validate_request(type_)
    async def index(data: Models) -> Models:
        return data

    test_client = app.test_client()
    response = await test_client.post("/", json=type_(name="bob", age=2))
    assert (await response.get_json()) == {"name": "bob", "age": 2}


@pytest.mark.parametrize("type_", [ADetails, DCDetails, MDetails, PyDetails, PyDCDetails, TDetails])
async def test_send_form(type_: Type[Models]) -> None:
    app = Quart(__name__)
    QuartSchema(app)

    @app.route("/", methods=["POST"])
    @validate_request(type_, source=DataSource.FORM)
    async def index(data: Models) -> Models:
        return data

    test_client = app.test_client()
    response = await test_client.post("/", form=type_(name="bob", age=2))
    assert (await response.get_json()) == {"name": "bob", "age": 2}


@given(st.builds(DCDetails))
async def test_hypothesis_dataclass(data: DCDetails) -> None:
    app = Quart(__name__)
    QuartSchema(app)

    @app.route("/", methods=["POST"])
    @validate_request(DCDetails)
    async def index(data: DCDetails) -> DCDetails:
        return data

    test_client = app.test_client()
    response = await test_client.post("/", json=data)
    assert response.status_code == 200
