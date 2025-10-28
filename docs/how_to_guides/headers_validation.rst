Headers Validation
==================

Headers are a mandatory part of a request or response that allow for
additional meta data describing the request or the response. It is
possible to validate that certain headers are present, or that if
headers are present they are of a certain type.

Request headers
---------------

Request headers can be validated against a schema you define by
decorating the route handler, as so,

.. tabs::

   .. tab:: attrs

      .. code-block:: python

         from attrs import define
         from quart_schema import validate_headers

         @define
         class Headers:
             x_required: str
             x_optional: int | None = None

         @app.route("/")
         @validate_headers(Headers)
         async def index(headers: Headers):
             ...

   .. tab:: dataclasses

      .. code-block:: python

         from dataclasses import dataclass

         from quart_schema import validate_headers

         @dataclass
         class Headers:
             x_required: str
             x_optional: int | None = None

         @app.route("/")
         @validate_headers(Headers)
         async def index(headers: Headers):
             ...

   .. tab:: msgspec

      .. code-block:: python

         from msgspec import Struct
         from quart_schema import validate_headers

         class Headers(Struct):
             x_required: str
             x_optional: int | None = None

         @app.route("/")
         @validate_headers(Headers)
         async def index(headers: Headers):
             ...

   .. tab:: pydantic

      .. code-block:: python

         from pydantic import BaseModel
         from quart_schema import validate_headers

         class Headers(BaseModel):
             x_required: str
             x_optional: int | None = None

         @app.route("/")
         @validate_headers(Headers)
         async def index(headers: Headers):
             ...

this will require the client adds a ``X-Required`` header to the
request and optionally ``X-Optional`` of type int.

If the client doesn't supply correctly structured data they will
receive a 400 (bad request) response without your route handler
running. If the client does supply correctly structured data it will
be passed into your route handler as the ``headers`` argument.

.. note::

   Additional headers are permitted and won't be passed in the
   ``headers`` argument. Use ``request.headers`` to access them.

   Header names are converted from snake_case to kebab-case as
   matching conventions.

Handling validation errors
~~~~~~~~~~~~~~~~~~~~~~~~~~

By default if the client sends headers that don't satisfy the schema a
400 bad request response will be sent. You can alter this by adding an
error handler, for example for a JSON error response,

.. code-block:: python

    from quart_schema import RequestSchemaValidationError

    @app.errorhandler(RequestSchemaValidationError)
    async def handle_request_validation_error():
        return {"error": "VALIDATION"}, 400

Response headers
----------------

Request headers can be validated alongside the response body bt
decorating the route handler with a relevant schema, as so,

.. tabs::

   .. tab:: attrs

      .. code-block:: python

         from attrs import define
         from quart_schema import validate_response

         @define
         class Headers:
             x_required: str
             x_optional: int | None = None

         @app.route("/")
         @validate_response(Body, 200, Headers)
         async def index():
             ...
             return body, 200, headers

   .. tab:: dataclasses

      .. code-block:: python

         from dataclasses import dataclass

         from quart_schema import validate_response

         @dataclass
         class Headers:
             x_required: str
             x_optional: int | None = None

         @app.route("/")
         @validate_response(Body, 200, Headers)
         async def index():
             ...
             return body, 200, headers

   .. tab:: msgspec

      .. code-block:: python

         from msgspec import Struct
         from quart_schema import validate_response

         class Headers(Struct):
             x_required: str
             x_optional: int | None = None

         @app.route("/")
         @validate_response(Body, 200, Headers)
         async def index():
             ...
             return body, 200, headers

   .. tab:: pydantic

      .. code-block:: python

         from pydantic import BaseModel
         from quart_schema import validate_response

         class Headers(BaseModel):
             x_required: str
             x_optional: int | None = None

         @app.route("/")
         @validate_response(Body, 200, Headers)
         async def index():
             ...
             return body, 200, headers

this will require that the headers variable adds a ``X-Required``
header to the response and optionally ``X-Optional`` of type int. The
headers object can be a dictionary (as with Quart) or a ``Headers``
instance.
