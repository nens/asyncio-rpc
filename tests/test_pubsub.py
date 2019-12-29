import pytest
import asyncio
from dataclasses import dataclass
from uuid import uuid4
from asyncio_rpc.server import RPCServer
from asyncio_rpc.client import RPCClient

from asyncio_rpc.models import RPCCall, RPCStack, RPCSubStack
from asyncio_rpc.client import WrappedException
from asyncio_rpc.server import DefaultExecutor
from .utils import rpc_commlayer
from asyncio_rpc.pubsub import Publisher

class Executor:
    """
    Default executor implementation, override if necessary
    """

    def __init__(self, namespace, instance):
        self.namespace = namespace
        self.instance = instance

    async def subscribe_call(self, publisher: Publisher):
        """
        Use the Publisher to publish results to the client
        """
        # if publisher.is_active:
        #     await publisher.publish(b'blaat')
        
        for i in range(0, 20):
            if publisher.is_active:
                print('publishing', i)
                await publisher.publish(i)
        await asyncio.sleep(5)
        for i in range(0, 20):
            print('pub2', i, publisher.is_active)
            await publisher.publish(i)       
        

    async def rpc_call(self, rpc_stack):
        print('RPC', rpc_stack)


@pytest.mark.asyncio
async def test_pubsub():

    rpc_client = RPCClient(await rpc_commlayer(b'pub', b'sub'))
    rpc_server = RPCServer(await rpc_commlayer(b'sub', b'pub'))
    executor = Executor('PUBSUB', None)
    rpc_server.register(executor)

    await rpc_server.rpc_commlayer.do_subscribe()

    rpc_func_call = RPCCall('get_item', [1], {})
    rpc_func_stack = RPCSubStack(
        uuid4().hex, 'PUBSUB', 300, [rpc_func_call])

    async def process_subscriber(rpc_func_stack):
        subscriber = await rpc_client.subscribe_call(rpc_func_stack)

        async for item in subscriber.enumerate():
            if item > 5:
                print('breaking', item)
                break
        print('deleting')
        await subscriber.close()

    funcs = [
        rpc_server.serve(),
        rpc_client.serve(),
        process_subscriber(rpc_func_stack)
    ]
    await asyncio.gather(*funcs)

    await rpc_client.rpc_commlayer.close()
    await rpc_server.rpc_commlayer.close()

