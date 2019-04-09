Dataclasses example
===================

The dataclasses example shows the code needed to expose the same 
'multiply' function as the basic example, only now the function
arguments are dataclasses and the function result is also
a dataclass.


Note: don't forget to register dataclasses, they won't be picked
up by the serialization/deserialization automatically.


Running example
---------------

- Run Redis on localhost.
- Execute from the root directory in two different terminals:

    >>> python3.7 -m examples.dataclass.server localhost
    >>> python3.7 -m examples.dataclass.client localhost
