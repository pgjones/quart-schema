Operation IDs
=============

Operation IDs are used by certain OpenAPI clients when consuming the API spec. These are
by default generated using the method and function name:

.. code-block:: python

    @app.get("/resource/")
    async def resource():
        ...

    @app.post("/resource/")
    async def create_resource():
        ...

would by default assign Operation IDs of ``get_resource`` and ``post_create_resource``
respectively. To have more fine-grained control, part of the Operation ID can be
overridden:

.. code-block:: python

    from quart_schema import operation_id

    @app.post("/resource/")
    @operation_id("make_resource")
    async def create_resource():
        ...

which would assign an Operation ID of ``post_make_resource`` to the route.
