Request Validation
==================

When receiving data from a client it makes sense to check that they've
sent it in a format you understand. This is done by validating the
request data is correct against a schema you define. Quart-Schema
allows validation of JSON data via decorating the route handler, as
so,

.. code-block:: python

    from dataclasses import dataclass

    from quart_schema import validate_request

    @dataclass
    class Todo:
        effort: int
        task: str

    @app.route("/", methods=["POST'])
    @validate_request(Todo)
    async def index(data: Todo):
        ...

this will expect the client to send a body with JSON structured to
match the Todo class, for example,

.. code-block:: json

    {
      "effort": 2,
      "task": "Finish the docs"
    }

If the client doesn't supply correctly structured data they will
receive a 400 (bad request) response without your route handler
running. If the client does supploy correctly structured data it will
be passed into your route handler as the ``data`` argument.

Form data
---------

By default the :func:`~quart_schema.validation.validate_request`
decorator assumes the request body is JSON encoded. If the request
body is form (application/x-www-form-urlencoded) encoded the
``source`` argument can be changed to validate the form data,

.. code-block:: python

    from dataclasses import dataclass

    from quart_schema import DataSource, validate_request

    @dataclass
    class Todo:
        effort: int
        task: str

    @app.route("/", methods=["POST'])
    @validate_request(Todo, source=DataSource.FORM)
    async def index(data: Todo):
        ...

with everything working as in the JSON example above.

.. note::

   Form encoded data is a flat structure, therefore Quart-Schema will
   raise a ``SchemaInvalidError`` if the model proposed has nested
   structures.

Files
-----

If your route receives files through a (multipart/form-data) encoded body, 
use the ``File`` class to check the request.

For a HTML form which accepts one or several files

.. code-block:: HTML

    <form action="/rich_post" method="POST" enctype="multipart/form-data">
        <input type="file" "name="images" multiple>
        <input type="file" name="video">
        <input type="text" name="text">
        <input type="submit" value="Submit">
    </form>

use a ``File`` or ``list[File]`` type hint to validate the request

.. code-block:: python

    from dataclasses import dataclass

    from quart_schema import DataSource, File, validate_request

    @dataclass
    class RichPost:
        images: list[File]
        video: File
        text: str

    @app.route("/rich_post", methods=["POST'])
    @validate_request(RichPost, source=DataSource.FORM)
    async def rich_post(data: RichPost):
        video = data.video.save(...)
        image = data.images[0].save(...)
        ...
