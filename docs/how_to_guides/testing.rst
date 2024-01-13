Testing
=======

You can test Quart-Schema validated routes the same way you'd test
normal Quart routes (everything works the same). In addition
Quart-Schema allows Pydantic models, or dataclasses to be sent via the
test client as ``json`` or ``form`` data, for example,

.. tabs::

   .. tab:: attrs

      .. code-block:: python

         from attrs import define

         @define
         class Details:
             name: str
             age: int | None = None

         @pytest.mark.asyncio
         async def test_send() -> None:
             ...
             test_client = app.test_client()
             response = await test_client.post("/", json=Details(name="bob", age=2))
             # Or
             response = await test_client.post("/", form=Details(name="bob", age=2))

   .. tab:: dataclasses

      .. code-block:: python

         from dataclasses import dataclass

         @dataclass
         class Details:
             name: str
             age: int | None = None

         @pytest.mark.asyncio
         async def test_send() -> None:
             ...
             test_client = app.test_client()
             response = await test_client.post("/", json=Details(name="bob", age=2))
             # Or
             response = await test_client.post("/", form=Details(name="bob", age=2))

   .. tab:: attrs

      .. code-block:: python

         from msgspec import Struct

         class Details(Struct):
             name: str
             age: int | None = None

         @pytest.mark.asyncio
         async def test_send() -> None:
             ...
             test_client = app.test_client()
             response = await test_client.post("/", json=Details(name="bob", age=2))
             # Or
             response = await test_client.post("/", form=Details(name="bob", age=2))

   .. tab:: pydantic

      .. code-block:: python

         from pydantic import BaseModel

         class Details(BaseModel):
             name: str
             age: int | None = None

         @pytest.mark.asyncio
         async def test_send() -> None:
             ...
             test_client = app.test_client()
             response = await test_client.post("/", json=Details(name="bob", age=2))
             # Or
             response = await test_client.post("/", form=Details(name="bob", age=2))


Hypothesis testing
------------------

It can be difficult to write test cases for complex structures that
cover all the edge cases (data state space). Hypothesis is a library
that can generate data for you that covers the edge cases. As
Hypothesis can infer how to construct type-annotated classes and
Pydantic ships a Hypothesis plugin for specific types it is possible
to test Quart-Schema routes with Hypothesis generated data, for
example,

.. code-block:: python

    from hypothesis import given, strategies as st
    from dataclasses import dataclass
    # Other imports not shown

    @dataclass
    class Details:
        name: str
        age: int | None = None

    @given(st.builds(Details))
    @pytest.mark.asyncio
    async def test_index(data: Details) -> None:
        app = Quart(__name__)
        QuartSchema(app)

        @app.route("/", methods=["POST"])
        @validate_request(Details)
        async def index(data: Details) -> Any:
            return data

        test_client = app.test_client()
        response = await test_client.post("/", json=data)
        assert response.status_code == 200

.. note::

    Hypothesis must be installed seperately.
