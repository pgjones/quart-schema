Convert camelCase JSON keys and snake_case variable names
=========================================================

Javascript and hence JSON have a convention of using camelCased key
names, whereas Python by convention uses snake_cased variabled
names. This causes problems with QuartSchema as by default the JSON
key name is the variable name. To convert between pass
``convert_casing=True`` when initialising QuartSchema, e.g.,

.. code-block:: python

    QuartSchema(app, convert_casing=True)

This will require that JSON sent to the app is camelCased and will
ensure that JSON returned from the app is camelCased and that the
OpenAPI schema is correct (also camelCased).
