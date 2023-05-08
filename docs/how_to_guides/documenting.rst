Document the API
================

To describe the API via an OpenAPI Info object pass the values
for the info argument in the extension constructor e.g.

.. code-block:: python

    from quart_schema import Info, QuartSchema

    quart_schema(app, info=Info(title="My Great API", version="0.1.0"))
    # Or alternatively
    quart_schema(app, info={"title": "My Great API", "version": "0.1.0"})

All the OpenAPI Info fields are allowed and will be validated by a
Pydantic model.

Hiding routes
-------------

To hide routes from the documentation use the
:func:`~quart_schema.extensions.hide` decorator, e.g.

.. code-block:: python

     from quart_schema import hide

     @app.route("/")
     @hide
     async def index():
         ...

Deprecating routes
------------------

To mark a route as deprecated use the
:func:`~quart_schema.extensions.deprecate` decorator, e.g.

.. code-block:: python

     from quart_schema import deprecate

     @app.route("/")
     @deprecate
     async def index():
         ...

Documenting without validation
------------------------------

The decorators
:func:`~quart_schema.documentation.document_querystring`,
:func:`~quart_schema.documentation.document_headers`,
:func:`~quart_schema.documentation.document_request`, and
:func:`~quart_schema.documentation.document_response` have the same
signatures and arguments as the validating equivalents but do no
validation. These can be used to simply document routes.
