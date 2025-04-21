Deprecating
===========

Deprecating allows routes to be marked as deprecated. Routes can be
deprecated using the :func:`~quart_schema.extensions.deprecate` decorator,

.. code-block:: python

    from quart_schema import deprecate

    @app.route("/v0/resource/")
    @deprecate
    async def get_resource():
        ...

blueprints can be deprecated using
:func:`~quart_schema.extensions.deprecate_blueprint` (applies to all routes
in the blueprint),

.. code-block:: python

    from quart_schema import deprecate_blueprint

    deprecate_blueprint(blueprint)
