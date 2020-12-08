Dataclass or BaseModel
======================

Pydantic's documentation primarily adopts the ``BaseModel`` approach,
i.e.

.. code-block:: python

    from pydantic import BaseModel

    class Item(BaseModel):
        ...

rather than the ``dataclass`` approach,

.. code-block:: python

    from pydantic.dataclasses import dataclass

    @dataclass
    class Item:
        ...

and whilst Quart-Schema supports both this documentation primarily
adopts the ``dataclass`` approach. This is because I find this
approach to be cleaner and clearer. I think if pydantic had started
when after ``dataclass`` was added to the Python stdlib it would have
done the same.

.. warning::

    Just a caveat, that these two approaches lead to potentially
    subtle differences which you can read about `here
    <https://github.com/samuelcolvin/pydantic/issues/710>`_.
