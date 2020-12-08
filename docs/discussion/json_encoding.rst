JSON Encoding
=============

By default Quart-Schema uses the pydantic JSON encoder (by changing
the encoder on the app). This can be altered by overriding this change
after initialising the Quart-Schema extension i.e.

.. code-block:: python

    QuartSchema(app)
    app.json_encoder = MyJSONEncoder  # To override

This is best as the pydantic decoder must be used (to create pydantic
models) and hence this ensures consistency.
