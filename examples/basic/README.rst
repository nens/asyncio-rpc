Basic example
=============

The basic example shows the code needed to expose a 'multiply' 
function via RPC.


Running example
---------------

- Run Redis on localhost.
- Execute from the root directory in two different terminals:

    >>> python3.7 -m examples.basic.server localhost
    >>> python3.7 -m examples.basic.client localhost
