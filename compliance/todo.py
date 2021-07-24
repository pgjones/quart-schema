from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from quart import Quart
from quart_schema import QuartSchema, validate_request, validate_response


app = Quart(__name__)
QuartSchema(app)


@dataclass
class Todo:
    "A TODO!"
    task: str
    due: Optional[datetime]


@app.post("/")
@validate_request(Todo)
@validate_response(Todo, 201)
async def create_todo(data: Todo) -> Todo:
    """Create a new todo"""
    pass
