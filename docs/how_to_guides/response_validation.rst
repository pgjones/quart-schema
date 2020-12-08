Response Validation
===================

When sending a JSON response to the client it makes sense to check
that the structure matches a predefined structure. This is a form of
`Design by Contract
<https://en.wikipedia.org/wiki/Design_by_contract>`_ and helps ensure
that your software works as expected. This is done by validating the
response data is correct against a schema you define. Quart-Schema
allows validation of JSON data via decorating the route handler, as
so,

.. code-block:: python

    from pydantic.dataclasses import dataclass

    from quart_schema import validate_response

    @dataclass
    class Todo:
        effort: int
        task: str

    @app.route("/")
    @validate_response(Todo)
    async def index():
        return data

will ensure that ``data`` represents or is a ``Todo`` object,
e.g. these responses are allowed. Note that the typical Quart response
return values are allowed, including status and headers,

.. code-block:: python

    return {"effort": 2, "task": "Finish the docs"}
    return Todo(effort=2, task="Finish the docs")
    return {"effort": 2, "task": "Finish the docs"}, 200
    return {"effort": 2, "task": "Finish the docs"}, {"X-Header": "value"}

.. note::

    The response validation is tied to the status code, which defaults
    to 200. This allows different response structures for different
    status codes as required.

Handling validation errors
--------------------------

By default if the response result doesn't satisfy the schema a
``ResponseSchemaValidationError`` error is raised and not handled,
resulting in a 500 internal server error response. You can alter this
by adding an error handler, for example,

.. code-block:: python

    from quart_schema import ResponseSchemaValidationError

    @app.errorhandler(ResponseSchemaValidationError)
    async def handle_response_validation_error():
        return {"error": "VALIDATION"}, 500
