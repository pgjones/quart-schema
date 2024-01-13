.. _validation_library:

Validation library choice
=========================

Quart-Schema is agnostic to your choice of validation library with
msgspec and Pydantic both supported. This choice must be made at
installation, with either the ``msgspec`` or ``pydantic`` extra used.

.. note::

   If you install both msgspec and Pydantic you can control which is
   used for builtin types by setting the
   ``QUART_SCHEMA_CONVERSION_PREFERENCE`` to either ``msgspec`` or
   ``pydantic``.

This documentation will show examples for both msgspec and Pydantic.

msgspec
-------

If you choose msgspec you can contruct the validation classes as
dataclasses, attrs definitions, or msgspec structs.

.. tabs::

   .. tab:: attrs

      .. code-block:: python

         from attrs import define

         @define
         class Person:
             name: str

   .. tab:: dataclasses

      .. code-block:: python

         from dataclasses import dataclass

         @dataclass
         class Person:
             name: str

   .. tab:: msgspec

      .. code-block:: python

         from msgspec import Struct

         class Person(Struct):
             name: str

Pydantic
--------

If you choose Pydantic you can contruct the validation classes as
dataclasses, Pydantic dataclasses, or BaseModels.

.. tabs::

   .. tab:: dataclasses

      .. code-block:: python

         from dataclasses import dataclass

         @dataclass
         class Person:
             name: str

   .. tab:: Pydantic dataclasses

      .. code-block:: python

         from pydantic.dataclasses import dataclass

         @dataclass
         class Person:
             name: str

   .. tab:: Pydantic BaseModel

      .. code-block:: python

         from pydantic import BaseModel

         class Person(BaseModel):
             name: str

Lists
-----

Note that lists are valid validation models i.e. the following is
valid for any of the above ``Person`` defintions,

.. code-block:: python

    from typing import List

    @validate_request(List[Person])
    @app.post("/")
    async def index():
        ...
