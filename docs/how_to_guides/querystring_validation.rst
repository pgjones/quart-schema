Querystring Validation
======================

The querystring is an optional part of the URL that allows for
parameters to be specified. It makes sense to check that they've sent
it in a format you understand. This is done by validating them against
a schema you define. Quart-Schema allows validation via decorating the
route handler, as so,

.. tabs::

   .. tab:: attrs

      .. code-block:: python

         from attrs import define
         from quart_schema import validate_querystring

         @define
         class Query:
             count_le: int | None = None
             count_gt: int | None = None

         @app.route("/")
         @validate_querystring(Query)
         async def index(query_args: Query):
             ...

   .. tab:: dataclasses

      .. code-block:: python

         from dataclasses import dataclass

         from quart_schema import validate_querystring

         @dataclass
         class Query:
             count_le: int | None = None
             count_gt: int | None = None

         @app.route("/")
         @validate_querystring(Query)
         async def index(query_args: Query):
             ...

   .. tab:: msgspec

      .. code-block:: python

         from msgspec import Struct
         from quart_schema import validate_querystring

         class Query(Struct):
             count_le: int | None = None
             count_gt: int | None = None

         @app.route("/")
         @validate_querystring(Query)
         async def index(query_args: Query):
             ...

   .. tab:: pydantic

      .. code-block:: python

         from pydantic import BaseModel
         from quart_schema import validate_querystring

         class Query(BaseModel):
             count_le: int | None = None
             count_gt: int | None = None

         @app.route("/")
         @validate_querystring(Query)
         async def index(query_args: Query):
             ...

this will allow the client to add a ``count_le``, ``count_gt``, or
both parameters to the URL e,g. ``/?count_le=2&count_gt=0``.

If the client doesn't supply correctly structured data they will
receive a 400 (bad request) response without your route handler
running. If the client does supply correctly structured data it will
be passed into your route handler as the ``query_args`` argument.

.. note::

   Querystring parameters must be optional defaulting to
   ``None`` (as querystrings are optional).

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

List values
-----------

You may want to allow a repeated, multiple, or list query string
parameter e.g. ``/?key=foo&key=bar``. Which can be done using
``list[str]`` for example.

For a field declared as a ``list``, the following forms are accepted
and equivalent,

- ``/?key=foo`` - a single value, treated as a one-element list
- ``/?key=foo&key=bar`` - repeated values
- ``/?key[]=foo&key[]=bar`` - the ``[]`` suffix convention (used e.g.
  by axios)

Parameters that are not declared as a list must only be given once;
repeating them (or adding the ``[]`` suffix) results in a 400
response.
