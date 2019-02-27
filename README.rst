Asyncio-rpc: Remote procedure calling framework
===============================================

The Python package for the asyncio remote procedure calling


.. image:: https://api.travis-ci.com/nens/asyncio-rpc.svg?branch=master
        :target: https://travis-ci.com/nens/asyncio-rpc/


.. image:: https://readthedocs.org/projects/httpsgithubcomnensasyncio-rpc/badge/?version=latest
        :target: https://httpsgithubcomnensasyncio-rpc.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status



* Free software: BSD license
* Documentation: https://httpsgithubcomnensasyncio-rpc.readthedocs.io.


Overview
========


Features
--------
 - Asyncio RPC client/server
 - Msgpack serialization with option to use own dataclasses (Python 3.7)
 - Redis communication layer
 - Other serialization methods and communication layers can be added


Testing
-------
docker-compose run pytest --cov=asyncio_rpc --cov-report=html