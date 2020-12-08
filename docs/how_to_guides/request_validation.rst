Request Validation
==================

When receiving data from a client it makes sense to check that they've
sent it in a format you understand. This is done by validating the
request data is correct against a schema you define. Quart-Schema
allows validation of JSON data via decorating the route handler, as
so,

.. code-block:: python

    from pydantic.dataclasses import dataclass

    from quart_schema import validate_request

    @dataclass
    class Todo:
        effort: int
        task: str

    @app.route("/", methods=["POST'])
    @validate_request(Todo)
    async def index(data: Todo):
        ...

this will expect the client to send a body with JSON structured to
match the Todo class, for example,

.. code-block:: json

    {
      "effort": 2,
      "task": "Finish the docs"
    }

If the client doesn't supply correctly structured data they will
receive a 400 (bad request) response without your route handler
running. If the client does supploy correctly structured data it will
be passed into your route handler as the ``data`` argument.

Handling validation errors
--------------------------

By default if the client sends a body that doesn't satisfy the schema
a 400 bad request response will be sent. You can alter this by adding
an error handler, for example for a JSON error response,

.. code-block:: python

    from quart_schema import RequestSchemaValidationError

    @app.errorhandler(RequestSchemaValidationError)
    async def handle_request_validation_error():
        return {"error": "VALIDATION"}, 400
