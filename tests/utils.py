from os import environ
from uuid import uuid4

from asyncio_rpc.commlayers.redis import RPCRedisCommLayer
from asyncio_rpc.models import RPCCall, RPCStack
from asyncio_rpc.serialization import msgpack as msgpack_serialization

# Set to env_var REDIS_HOST or 'localhost' as default
REDIS_HOST = environ.get("REDIS_HOST", "localhost")


class CustomException(Exception):
    pass


class Service(object):
    """
    Testing service that is register via the TestExecutor
    on the RPCServer
    """

    def __init__(self):
        self.data = {"foo": "bar"}

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
        rpc_func_call = RPCCall("multiply", [x], {"y": y})
        rpc_func_stack = RPCStack(uuid4().hex, "TEST", 300, [rpc_func_call])
        return await self.client.rpc_call(rpc_func_stack)

    async def get_item(self, key):
        rpc_func_call = RPCCall("get_item", [key], {})
        rpc_func_stack = RPCStack(uuid4().hex, "TEST", 300, [rpc_func_call])
        return await self.client.rpc_call(rpc_func_stack)

    async def custom_error(self):
        rpc_func_call = RPCCall("custom_error", [], {})
        rpc_func_stack = RPCStack(uuid4().hex, "TEST", 300, [rpc_func_call])
        return await self.client.rpc_call(rpc_func_stack)


async def stop_rpc_server_on_result_of(
    async_func, rpc_server, rpc_client, client_processing=False
):
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
        await rpc_server.queue.put(b"END")
        await rpc_server.rpc_commlayer.unsubscribe()

        if client_processing:
            await rpc_client.queue.put(b"END")
            await rpc_client.rpc_commlayer.unsubscribe()

    # Return the result
    return result


async def rpc_commlayer(subchannel, pubchannel, host=REDIS_HOST):
    """
    Get a RPCRedisCommLayer with subchannel/pubchannel
    """
    return await RPCRedisCommLayer.create(
        subchannel=subchannel,
        pubchannel=pubchannel,
        host=host,
        serialization=msgpack_serialization,
    )
