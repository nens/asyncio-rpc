import pytest

from tests.utils import (
    rpc_client as rpc_client_fixture
)

from asyncio_rpc.models import RPCMessage

rpc_client = rpc_client_fixture


async def stop_rpc_client_on_rpc_message(rpc_client, expected_rpc_message):
    async def on_rpc_message(rpc_message: RPCMessage, channel):
        assert isinstance(rpc_message, RPCMessage)

        await rpc_client.queue.put(b'END')
        await rpc_client.rpc_commlayer.unsubscribe()

        assert rpc_message == expected_rpc_message

    return on_rpc_message


@pytest.mark.asyncio
async def test_rpc_message(rpc_client):
    await rpc_client.rpc_commlayer.do_subscribe()

    rpc_message = RPCMessage(
        uid='1', namespace='TEST', data={'foo': 'bar'})

    # publish to self
    await rpc_client.rpc_commlayer.publish(
        rpc_message, channel=rpc_client.rpc_commlayer.subchannel)

    await rpc_client.serve(
        on_rpc_message=await stop_rpc_client_on_rpc_message(
            rpc_client, rpc_message))

    await rpc_client.rpc_commlayer.close()
