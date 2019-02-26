import pytest

from tests.utils import (
    Executor, rpc_server as rpc_server_fixture
)
from asyncio_rpc.server import NamespaceError
from asyncio_rpc.models import RPCStack

rpc_server = rpc_server_fixture


@pytest.mark.asyncio
async def test_registration(rpc_server):
    rpc_server.register(Executor(None))
    await rpc_server.rpc_commlayer.close()


@pytest.mark.asyncio
async def test_double_registration_error(rpc_server):
    rpc_server.register(Executor(None))

    with pytest.raises(NamespaceError):
        rpc_server.register(Executor(None))

    await rpc_server.rpc_commlayer.close()


@pytest.mark.asyncio
async def test_unknown_namespace_error(rpc_server):
    with pytest.raises(NamespaceError):
        await rpc_server.rpc_call(
            RPCStack(uid='1', namespace='UNKNOWN', stack=[], timeout=300))

    await rpc_server.rpc_commlayer.close()
