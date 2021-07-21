Request Validation
==================

When receiving data from a client it makes sense to check that they've
sent it in a format you understand. This is done by validating the
request data is correct against a schema you define. Quart-Schema
allows validation of JSON data via decorating the route handler, as
so,

.. code-block:: python

    from dataclasses import dataclass

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

Form data
---------

By default the :func:`~quart_schema.validation.validate_request`
decorator assumes the request body is JSON encoded. If the request
body is form (application/x-www-form-urlencoded) encoded the
``source`` argument can be changed to validate the form data,

.. code-block:: python

    from dataclasses import dataclass

    from quart_schema import DataSource, validate_request

    @dataclass
    class Todo:
        effort: int
        task: str

    @app.route("/", methods=["POST'])
    @validate_request(Todo, source=DataSource.FORM)
    async def index(data: Todo):
        ...

with everything working as in the JSON example above.

.. note::

   Form encoded data is a flat structure, therefore Quart-Schema will
   raise a ``SchemaInvalidError`` if the model proposed has nested
   structures.
