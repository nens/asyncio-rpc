import asyncio
from uuid import uuid4
from argparse import ArgumentParser
from asyncio_rpc.client import RPCClient
from asyncio_rpc.models import RPCCall, RPCStack
from asyncio_rpc.commlayers.redis import RPCRedisCommLayer
from asyncio_rpc.serialization import msgpack as msgpack_serialization


class ServiceClient:
    def __init__(self, client: RPCClient, namespace=None):
        assert namespace is not None
        assert client is not None
        self.client = client
        self.namespace = namespace

    async def _rpc_call(self, func_name, func_args, func_kwargs):
        rpc_func_call = RPCCall(func_name, func_args, func_kwargs)
        rpc_func_stack = RPCStack(
            uuid4().hex, self.namespace, 300, [rpc_func_call])

        return await self.client.rpc_call(rpc_func_stack)

    async def multiply(self, x, y):
        return await self._rpc_call(
            func_name='multiply', func_args=[x, y], func_kwargs={})


async def main(args):
    rpc_commlayer = await RPCRedisCommLayer.create(
            subchannel=b'sub', pubchannel=b'pub',
            host=args.redis_host, serialization=msgpack_serialization)

    rpc_client = RPCClient(rpc_commlayer)

    service_client = ServiceClient(rpc_client, 'TEST')

    result = await service_client.multiply(100, 100)

    print(result)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('redis_host', metavar='H', type=str,
                        help='Redis host IP address')
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(args))
