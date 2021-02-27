from typing import Any, Optional

import pytest
from pydantic import BaseModel
from pydantic.dataclasses import dataclass
from quart import Quart

from quart_schema import QuartSchema


@dataclass
class DCDetails:
    name: str
    age: Optional[int] = None


class Details(BaseModel):
    name: str
    age: Optional[int]


@pytest.mark.asyncio
@pytest.mark.parametrize("type_", [DCDetails, Details])
async def test_make_response(type_: Any) -> None:
    app = Quart(__name__)
    QuartSchema(app)

    @app.route("/")
    async def index() -> Any:
        return type_(name="bob", age=2)

    test_client = app.test_client()
    response = await test_client.get("/")
    assert (await response.get_json()) == {"name": "bob", "age": 2}
