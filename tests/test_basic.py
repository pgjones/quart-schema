from pathlib import Path
from typing import Type, Union
from uuid import UUID

import pytest
from pydantic import BaseModel
from quart import Quart, ResponseReturnValue

from quart_schema import QuartSchema
from .helpers import ADetails, DCDetails, MDetails, PyDCDetails, PyDetails, TDetails


@pytest.mark.parametrize("type_", [ADetails, DCDetails, MDetails, PyDetails, PyDCDetails, TDetails])
async def test_make_response(
    type_: Type[Union[ADetails, DCDetails, MDetails, PyDetails, PyDCDetails, TDetails]],
) -> None:
    app = Quart(__name__)
    QuartSchema(app)

    @app.route("/")
    async def index() -> ResponseReturnValue:
        return type_(name="bob", age=2)  # type: ignore

    test_client = app.test_client()
    response = await test_client.get("/")
    assert (await response.get_json()) == {"name": "bob", "age": 2}


async def test_make_response_no_model() -> None:
    app = Quart(__name__)
    QuartSchema(app)

    @app.route("/")
    async def index() -> ResponseReturnValue:
        return {"name": "bob", "age": 2}, {"Content-Type": "application/json", "X-1": "2"}

    test_client = app.test_client()
    response = await test_client.get("/")
    assert (await response.get_json()) == {"name": "bob", "age": 2}
    assert response.headers["Content-Type"] == "application/json"
    assert response.headers["X-1"] == "2"


class PydanticEncoded(BaseModel):
    a: UUID
    b: Path


async def test_make_pydantic_encoder_response() -> None:
    app = Quart(__name__)
    QuartSchema(app)

    @app.route("/")  # type: ignore
    async def index() -> PydanticEncoded:
        return PydanticEncoded(a=UUID("23ef2e02-1c20-49de-b05e-e9fe2431c474"), b=Path("/"))

    test_client = app.test_client()
    response = await test_client.get("/")
    assert (await response.get_json()) == {"a": "23ef2e02-1c20-49de-b05e-e9fe2431c474", "b": "/"}
