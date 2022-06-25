.. _quickstart:

Quickstart
==========

Lets take a simple Todo example, whereby we want to define a ``Todo``
object to be validated,

.. code-block:: python
    :caption: schema.py

    from dataclasses import dataclass
    from datetime import datetime
    from typing import Optional

    from quart import Quart
    from quart_schema import QuartSchema, validate_request, validate_response

    app = Quart(__name__)
    QuartSchema(app)

    @dataclass
    class Todo:
        task: str
        due: Optional[datetime]

    @app.route("/", methods=["POST"])
    @validate_request(Todo)
    @validate_response(Todo, 201)
    async def create_todo(data: Todo) -> tuple[Todo, int]:
        """Create a Todo"""
        # Do something with data, e.g. save to the DB
        ...
        return data, 201

and is simply run via

.. code-block:: console

    python schema.py

or alternatively

.. code-block:: console

    $ export QUART_APP=schema:app
    $ quart run

and tested by

.. code-block:: sh

    curl -v -H "content-type: application/json" -d '{"due":"2020-12-08T11:19:35.818445","task":"Build an example"}' localhost:5000/

with the docs available at

.. code-block::

    localhost:5000/docs

or

.. code-block::

    localhost:5000/redocs
