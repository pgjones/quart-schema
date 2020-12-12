Querystring Validation
======================

The querystring is an optional part of the URL that allows for
parameters to be specified. It makes sense to check that they've sent
it in a format you understand. This is done by validating them against
a schema you define. Quart-Schema allows validation via decorating the
route handler, as so,

.. code-block:: python

    from pydantic.dataclasses import dataclass

    from quart_schema import validate_querystring

    @dataclass
    class Query:
        count_le: Optional[int] = None
        count_gt: Optional[int] = None

    @app.route("/")
    @validate_querystring(Query)
    async def index(query_args: Query):
        ...

this will allow the client to add a ``count_le``, ``count_gt``, or
both parameters to the URL e,g. ``/?count_le=2&count_gt=0``.

Note that querystring parameters must be optional defaulting to
``None`` (as querystrings are optional).

If the client doesn't supply correctly structured data they will
receive a 400 (bad request) response without your route handler
running. If the client does supploy correctly structured data it will
be passed into your route handler as the ``query_args`` argument.

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
