Tagging
=======

Tagging allows routes to be grouped, based on a name (tag). Routes can
be tagged using the :func:`~quart_schema.extensions.tag` decorator,

.. code-block:: python

    from quart_schema import tag

    @app.route("/v0/resource/")
    @tag(["v0"])
    async def get_resource():
        ...

with global descriptions added to the openapi specification,

.. code-block:: python

    from quart_schema import QuartSchema

    QuartSchema(app, tags=[{"name": "v0", "description": "The first API version"}])

    ...
