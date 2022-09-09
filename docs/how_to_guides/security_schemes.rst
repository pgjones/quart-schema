Security schemes
================

OpenAPI authentication or security schemes can be specified indicating
to users how they should authenticate. To do so a security requirement
and security scheme should be defined as extension arguments. For
example for a security tagged ``app_id`` that comprises of an API key
passed as a querry arg called ``appID``:

.. code-block:: python

    from quart_schema import QuartSchema

    QuartSchema(
        app,
        security={"app_id": []},
        security_schemes={
            "app_id": {"type": "apiKey", "name": "appID", "in": "query"}
        },
    )

This will then apply to all routes unless overridden. For example to
remove security from a route:

.. code-block:: python

    from quart_schema import security_scheme

    @app.get("/")
    @security_scheme([])
    async def route():
        ...

.. warning::

   Security schemes are for documentation only, they do no
   authentication and should not be relied on for security.
