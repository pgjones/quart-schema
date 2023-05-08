JSON Encoding & Decoding
========================

By default Quart-Schema extends the DefaultJSONProvider to use the
pydantic encoder if the value cannot be encoded. This can be altered
by overriding this change after initialising the Quart-Schema
extension i.e.

.. code-block:: python

    QuartSchema(app)
    app.json_encoder = MyJSONEncoder  # To override

This is best as the pydantic decoder must be used (to create pydantic
models) and hence this ensures consistency.
