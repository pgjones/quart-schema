from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from quart import Quart
from quart_schema import QuartSchema, validate_querystring, validate_request, validate_response


app = Quart(__name__)
QuartSchema(app)


@dataclass
class Todo:
    "A TODO!"
    task: str
    due: Optional[datetime]


@dataclass
class Options:
    complete: Optional[bool] = None


@app.post("/")
@validate_querystring(Options)
@validate_request(Todo)
@validate_response(Todo, 201)
async def create_todo(data: Todo, query_args: Options) -> Todo:
    """Create a new todo"""
    pass
