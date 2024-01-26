Quart-Schema
============

|Build Status| |docs| |pypi| |python| |license|

Quart-Schema is a Quart extension that provides schema validation and
auto-generated API documentation. This is particularly useful when
writing RESTful APIs.

Quart-Schema can use either `msgspec
<https://jcristharif.com/msgspec>`_ or `pydantic
<https://docs.pydantic.dev>`_ to validate.

Quickstart
----------

Quart-Schema can validate an existing Quart route by decorating it
with ``validate_querystring``, ``validate_request``, or
``validate_response``. It can also validate the JSON data sent and
received over websockets using the ``send_as`` and ``receive_as``
methods.

.. code-block:: python

    from dataclasses import dataclass
    from datetime import datetime

    from quart import Quart, websocket
    from quart_schema import QuartSchema, validate_request, validate_response

    app = Quart(__name__)
    QuartSchema(app)

    @dataclass
    class Todo:
        task: str
        due: datetime | None

    @app.post("/")
    @validate_request(Todo)
    @validate_response(Todo, 201)
    async def create_todo(data: Todo) -> tuple[Todo, int]:
        ... # Do something with data, e.g. save to the DB
        return data, 201

    @app.websocket("/ws")
    async def ws() -> None:
        while True:
            data = await websocket.receive_as(Todo)
            ... # Do something with data, e.g. save to the DB
            await websocket.send_as(data, Todo)

The documentation is served by default at ``/openapi.json`` according
to the OpenAPI standard, or at ``/docs`` for a `SwaggerUI
<https://swagger.io/tools/swagger-ui/>`_ interface, or ``/redocs`` for
a `redoc <https://github.com/Redocly/redoc>`_ interface, or
``/scalar`` for a `Scalar <https://github.com/scalar/scalar>`_
interface. Note that there is currently no documentation standard for
WebSockets.

Contributing
------------

Quart-Schema is developed on `GitHub
<https://github.com/pgjones/quart-schema>`_. If you come across an
issue, or have a feature request please open an `issue
<https://github.com/pgjones/quart-schema/issues>`_. If you want to
contribute a fix or the feature-implementation please do (typo fixes
welcome), by proposing a `merge request
<https://github.com/pgjones/quart-schema/merge_requests>`_.

Testing
~~~~~~~

The best way to test Quart-Schema is with `Tox
<https://tox.readthedocs.io>`_,

.. code-block:: console

    $ pip install tox
    $ tox

this will check the code style and run the tests.

Help
----

The Quart-Schema `documentation
<https://quart-schema.readthedocs.io>`_ is the best places to
start, after that try searching `stack overflow
<https://stackoverflow.com/questions/tagged/quart>`_ or ask for help
`on gitter <https://gitter.im/python-quart/lobby>`_. If you still
can't find an answer please `open an issue
<https://github.com/pgjones/quart-schema/issues>`_.


.. |Build Status| image:: https://github.com/pgjones/quart-schema/actions/workflows/ci.yml/badge.svg
   :target: https://github.com/pgjones/quart-schema/commits/main

.. |docs| image:: https://img.shields.io/badge/docs-passing-brightgreen.svg
   :target: https://quart-schema.readthedocs.io

.. |pypi| image:: https://img.shields.io/pypi/v/quart-schema.svg
   :target: https://pypi.python.org/pypi/Quart-Schema/

.. |python| image:: https://img.shields.io/pypi/pyversions/quart-schema.svg
   :target: https://pypi.python.org/pypi/Quart-Schema/

.. |license| image:: https://img.shields.io/badge/license-MIT-blue.svg
   :target: https://github.com/pgjones/quart-schema/blob/main/LICENSE
