Headers Validation
==================

Headers are a mandatory part of a request that allow for additional
meta data describing the request. It is possible to validate that
certain headers are present, or that if headers are present they are
of a certain type. This is done by validating them against a schema
you define. Quart-Schema allows validation via decorating the route
handler, as so,

.. code-block:: python

    from dataclasses import dataclass

    from quart_schema import validate_headers

    @dataclass
    class Headers:
        x_required: str
        x_optional: Optional[int] = None

    @app.route("/")
    @validate_headers(Headers)
    async def index(headers: Headers):
        ...

this will require the client adds a ``X-Required`` header to the
request and optionally ``X-Optional`` of type int.

If the client doesn't supply correctly structured data they will
receive a 400 (bad request) response without your route handler
running. If the client does supploy correctly structured data it will
be passed into your route handler as the ``headers`` argument.

.. note::

   Additional headers are permitted and won't be passed in the
   ``headers`` argument. Use ``request.headers`` to access them.

   Header names are converted from snake_case to kebab-case as
   matching conventions.

Handling validation errors
--------------------------

By default if the client sends headers that don't satisfy the schema a
400 bad request response will be sent. You can alter this by adding an
error handler, for example for a JSON error response,

.. code-block:: python

    from quart_schema import RequestSchemaValidationError

    @app.errorhandler(RequestSchemaValidationError)
    async def handle_request_validation_error():
        return {"error": "VALIDATION"}, 400
