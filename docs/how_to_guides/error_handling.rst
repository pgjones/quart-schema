Handling validation errors
==========================

By default if the client sends a body that doesn't satisfy the schema
a 400 bad request response will be sent. You can alter this by adding
an error handler, for example for a JSON error response,

.. code-block:: python

    from quart_schema import RequestSchemaValidationError

    @app.errorhandler(RequestSchemaValidationError)
    async def handle_request_validation_error(error):
        return {"error": "VALIDATION"}, 400

or if you prefer to let the requestor know exactly why the validation
failed you can utilise the ``validation_error`` attribute which is a
either Pydantic ``ValidationError``, a msgspec ``ValidationError`` or
a ``TypeError``,

.. code-block:: python

    from quart_schema import RequestSchemaValidationError

    @app.errorhandler(RequestSchemaValidationError)
    async def handle_request_validation_error(error):
        return {
          "errors": str(error.validation_error),
        }, 400
