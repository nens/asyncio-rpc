Asyncio-rpc: Remote procedure calling framework
===============================================

The Python package for the asyncio remote procedure calling

.. image:: https://github.com/nens/asyncio-rpc/actions/workflows/test.yml/badge.svg?branch=master
        :target: https://github.com/nens/asyncio-rpc/actions/workflows/test.yml

.. image:: https://readthedocs.org/projects/asyncio-rpc/badge/?version=latest
        :target: https://asyncio-rpc.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status



* Free software: BSD license
* Documentation: https://asyncio-rpc.readthedocs.io.


Overview
========


Features
--------
 - Asyncio RPC client/server
 - Msgpack serialization with option to use own dataclasses (Python 3.10)
 - Redis communication layer
 - Other serialization methods and communication layers can be added


Examples
--------

The examples can be run from this directory, for the dataclass example 
(using localhost as redis host):

    >>> python3.8 -m examples.dataclass.server localhost
    >>> python3.8 -m examples.dataclass.client localhost


Testing
-------
    >>> docker compose run asyncio_rpc pytest --cov=asyncio_rpc --cov-report=html
