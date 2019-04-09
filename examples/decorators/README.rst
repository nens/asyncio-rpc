Decorator example
=================

The decorator example shows the code needed to expose the same 
'multiply' function as the basic example, only now the client side
methods can be decoratored.


Running example
---------------

- Run Redis on localhost.
- Execute from the root directory in two different terminals:

    >>> python3.7 -m examples.decorators.server localhost
    >>> python3.7 -m examples.decorators.client localhost
