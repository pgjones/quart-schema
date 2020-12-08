WebSocket Validation
====================

Messages sent and received over a WebSocket connection can be
stringified-JSON and these JSON objects can be validated against
schemas much like the request and response bodies. To do so
Quart-Schema changes the default WebSocket class to add
:meth:`~quart_schema.WebsocketMixin.receive_as` and
:meth:`~quart_schema.WebsocketMixin.send_as` methods. Which can be
used,

.. code-block:: python

    from pydantic.dataclasses import dataclass

    from quart import websocket

    @dataclass
    class Todo:
        effort: int
        task: str

    @app.websocket("/ws")
    async def ws():
        data: Todo = await websocket.receive_as(Todo)
        await websocket.send_as(data, Todo)

Handling validation errors
--------------------------

If the received message or sent data doesn't satisfy the schema a
``SchemaValidationError`` will be raised directly. This can be handled
or left (which closes the connection), e.g.

.. code-block:: python

    @app.websocket("/ws")
    async def ws():
        try:
            data: Todo = await websocket.receive_as(Todo)
        except SchemaValidationError:
            ... # do something
