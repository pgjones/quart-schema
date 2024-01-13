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

.. tabs::

   .. tab:: attrs

      .. code-block:: python

         from attrs import define
         from quart_schema import validate_response

         @define
         class Todo:
             effort: int
             task: str

         @app.route("/")
         @validate_response(Todo)
         async def index():
             return data

   .. tab:: dataclasses

      .. code-block:: python

         from dataclasses import dataclass

         from quart_schema import validate_response

         @dataclass
         class Todo:
             effort: int
             task: str

         @app.route("/")
         @validate_response(Todo)
         async def index():
             return data

   .. tab:: attrs

      .. code-block:: python

         from msgspec import Struct
         from quart_schema import validate_response

         class Todo(Struct):
             effort: int
             task: str

         @app.route("/")
         @validate_response(Todo)
         async def index():
             return data

   .. tab:: pydantic

      .. code-block:: python

         from pydantic import BaseModel
         from quart_schema import validate_response

         class Todo(BaseModel):
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

Handling multiple/different status codes
----------------------------------------

The :func:`~quart_schema.validation.validate_response` decorator's
second argument is the status code the validation applies too. By
default this is assumed to be ``200``, but can be changed to validate
responses that are sent with a different status code.

To validate a route that returns different different responses by
status code the decorator can be used multiple times,

.. code-block:: python

    @app.route("/")
    @validate_response(Todo, 200)
    @validate_response(CreatedTodo, 201)
    async def index():
        if ...:
            return Todo(), 200
        else:
            return CreatedTodo(), 201

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
