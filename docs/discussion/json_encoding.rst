JSON Encoding & Decoding
========================

By default Quart-Schema uses the pydantic JSON encoder (by changing
the encoder on the app). This can be altered by overriding this change
after initialising the Quart-Schema extension i.e.

.. code-block:: python

    QuartSchema(app)
    app.json_encoder = MyJSONEncoder  # To override

This is best as the pydantic decoder must be used (to create pydantic
models) and hence this ensures consistency.

If you are using the casing conversion feature the
``app.json_decoder`` will also be set to a specific Quart-Schema
version.
