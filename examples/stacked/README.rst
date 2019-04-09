Stacked example
===============

The stacked example shows the code needed to expose the same 
'multiply' function as the basic example, only now allowing
to execute stacked function calls like:

res = service_client.integer.multiply(100, 100)


Running example
---------------

- Run Redis on localhost.
- Execute from the root directory in two different terminals:

    >>> python3.7 -m examples.stacked.server localhost
    >>> python3.7 -m examples.stacked.client localhost
