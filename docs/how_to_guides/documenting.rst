Controlling the documentation
=============================

To hide routes from the documentation use the
:func:`~quart_schema.extensions.hide_route` decorator, e.g.

.. code-block:: python

     from quart_schema import hide_route

     @app.route("/")
     @hide_route
     async def index():
         ...
