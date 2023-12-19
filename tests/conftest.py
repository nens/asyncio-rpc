import pytest
import asyncio

from .utils import rpc_commlayer, stop_rpc_server_on_result_of
from asyncio_rpc.server import RPCServer
from asyncio_rpc.client import RPCClient
from asyncio_rpc.serialization import msgpack as msgpack_serialization


@pytest.fixture
async def rpc_client():
    return RPCClient(await rpc_commlayer(b"pub", b"sub"))


@pytest.fixture
async def rpc_server():
    return RPCServer(await rpc_commlayer(b"sub", b"pub"))


@pytest.fixture()
def serialize_deserialize():
    def func(value, strict_map_key=True):
        return msgpack_serialization.loadb(
            msgpack_serialization.dumpb(value), strict_map_key=strict_map_key)

    return func


@pytest.fixture
async def do_rpc_call():
    async def wrapper(
        service_client, executor, func, custom_dataclasses=[], client_processing=False
    ):
        # Initialize both client & server
        rpc_client = RPCClient(await rpc_commlayer(b"pub", b"sub"))
        rpc_server = RPCServer(await rpc_commlayer(b"sub", b"pub"))

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
                func, rpc_server, rpc_client, client_processing
            ),
            rpc_server.serve(),
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