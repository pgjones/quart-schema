from dataclasses import dataclass
from typing import Optional

import pytest
from pydantic import BaseModel
from pydantic.dataclasses import dataclass as pydantic_dataclass
from quart import Quart

from quart_schema import QuartSchema, ResponseReturnValue
from quart_schema.typing import PydanticModel


@dataclass
class DCDetails:
    name: str
    age: Optional[int] = None


class Details(BaseModel):
    name: str
    age: Optional[int]


@pydantic_dataclass
class PyDCDetails:
    name: str
    age: Optional[int] = None


@pytest.mark.asyncio
@pytest.mark.parametrize("type_", [DCDetails, Details, PyDCDetails])
async def test_make_response(type_: PydanticModel) -> None:
    app = Quart(__name__)
    QuartSchema(app)

    @app.route("/")
    async def index() -> ResponseReturnValue:
        return type_(name="bob", age=2)

    test_client = app.test_client()
    response = await test_client.get("/")
    assert (await response.get_json()) == {"name": "bob", "age": 2}
