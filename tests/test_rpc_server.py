import pytest

from asyncio_rpc.models import RPCStack
from asyncio_rpc.server import DefaultExecutor, NamespaceError, RPCServer


class MockService:
    pass


async def test_registration(rpc_server: RPCServer):
    rpc_server.register(DefaultExecutor("TEST", MockService()))
    await rpc_server.rpc_commlayer.close()


async def test_double_registration_error(rpc_server: RPCServer):
    rpc_server.register(DefaultExecutor("TEST", MockService()))

    with pytest.raises(NamespaceError):
        rpc_server.register(DefaultExecutor("TEST", MockService()))

    await rpc_server.rpc_commlayer.close()


async def test_unknown_namespace_error(rpc_server: RPCServer):
    with pytest.raises(NamespaceError):
        await rpc_server.rpc_call(
            RPCStack(uid="1", namespace="UNKNOWN", stack=[], timeout=300)
        )

    await rpc_server.rpc_commlayer.close()
