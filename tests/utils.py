import pytest
import asyncio

from os import environ
from uuid import uuid4


from asyncio_rpc.serialization import msgpack as msgpack_serialization

from asyncio_rpc.server import RPCServer
from asyncio_rpc.client import RPCClient
from asyncio_rpc.models import RPCCall, RPCStack
from asyncio_rpc.commlayers.redis import RPCRedisCommLayer

# Set to env_var REDIS_HOST or 'localhost' as default
REDIS_HOST = environ.get('REDIS_HOST', 'localhost')


async def rpc_commlayer(subchannel, pubchannel, host=REDIS_HOST):
    """
    Get a RPCRedisCommLayer with subchannel/pubchannel
    """
    return await RPCRedisCommLayer.create(
            subchannel=subchannel, pubchannel=pubchannel,
            host=host, serialization=msgpack_serialization)


class CustomException(Exception):
    pass


class Service(object):
    """
    Testing service that is register via the TestExecutor
    on the RPCServer
    """

    def __init__(self):
        self.data = {'foo': 'bar'}

    def multiply(self, x, y=1):
        return x * y

    def get_item(self, key):
        return self.data[key]

    def custom_error(self):
        raise CustomException("Foobar")


class ServiceClient(object):
    """
    TestService client, exposing (rpc) functions
    that can be called on the TestService instance.
    """
    def __init__(self, client):

        self.client = client

    async def multiply(self, x, y=100):
        rpc_func_call = RPCCall('multiply', [x], {'y': y})
        rpc_func_stack = RPCStack(
            uuid4().hex, 'TEST', 300, [rpc_func_call])
        return await self.client.rpc_call(rpc_func_stack)

    async def get_item(self, key):
        rpc_func_call = RPCCall('get_item', [key], {})
        rpc_func_stack = RPCStack(
            uuid4().hex, 'TEST', 300, [rpc_func_call])
        return await self.client.rpc_call(rpc_func_stack)

    async def custom_error(self):
        rpc_func_call = RPCCall('custom_error', [], {})
        rpc_func_stack = RPCStack(
            uuid4().hex, 'TEST', 300, [rpc_func_call])
        return await self.client.rpc_call(rpc_func_stack)


async def stop_rpc_server_on_result_of(
        async_func, rpc_server, rpc_client, client_processing=False):
    """
    awaits the given async_func.
    stops the rpc_server (background) processing on result,
    allowing the rpc_server.serve() to return.
    """
    # Await func result

    try:
        result = await async_func
    finally:
        # Stop listening and queue processing in server,
        # allowing rpc_serve.serve() to return
        await rpc_server.queue.put(b'END')
        await rpc_server.rpc_commlayer.unsubscribe()

        if client_processing:
            await rpc_client.queue.put(b'END')
            await rpc_client.rpc_commlayer.unsubscribe()

    # Return the result
    return result


@pytest.fixture
async def rpc_client():
    return RPCClient(await rpc_commlayer(b'pub', b'sub'))


@pytest.fixture
async def rpc_server():
    return RPCServer(await rpc_commlayer(b'sub', b'pub'))


@pytest.fixture
async def do_rpc_call():
    async def wrapper(service_client, executor, func, custom_dataclasses=[],
                      client_processing=False):
        # Initialize both client & server
        rpc_client = RPCClient(await rpc_commlayer(b'pub', b'sub'))
        rpc_server = RPCServer(await rpc_commlayer(b'sub', b'pub'))

        service_client.client = rpc_client
        rpc_server.register(executor)

        # Register any given custom dataclasses on both ends
        rpc_client.register_models(custom_dataclasses)
        rpc_server.register_models(custom_dataclasses)

        # Already start subscribing, to be sure
        # we don't miss a message
        await rpc_server.rpc_commlayer.do_subscribe()

        # Execute rpc call and stop rpc_server when
        # a result has been returned
        async_funcs = [
            stop_rpc_server_on_result_of(
                func, rpc_server, rpc_client, client_processing),
            rpc_server.serve()
        ]

        # Add rpc_client.serve if client processing
        if client_processing:
            async_funcs.append(rpc_client.serve())

        try:
            result = (await asyncio.gather(*async_funcs))[0]
        finally:
            # Close all rpc_commlayers
            await rpc_client.rpc_commlayer.close()
            await rpc_server.rpc_commlayer.close()

        return result

    return wrapper
