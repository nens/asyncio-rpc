import asyncio
from uuid import uuid4
from argparse import ArgumentParser
from asyncio_rpc.client import RPCClient
from asyncio_rpc.models import RPCCall, RPCStack
from asyncio_rpc.commlayers.redis import RPCRedisCommLayer
from asyncio_rpc.serialization import msgpack as msgpack_serialization


def rpc_method(func):
    def rpc_method(self, *args, **kwargs):
        rpc_func_call = RPCCall(func.__name__, args, kwargs)
        rpc_func_stack = RPCStack(
            uuid4().hex, self.namespace, 300, [rpc_func_call])
        return self.client.rpc_call(rpc_func_stack)
    rpc_method._is_rpc_method = True
    return rpc_method


class ServiceClient:
    def __init__(self, client: RPCClient, namespace=None):
        assert namespace is not None
        assert client is not None
        self.client = client
        self.namespace = namespace

    @rpc_method
    async def multiply(self, x, y):
        """
        The decorator takes care of sending the function
        name & params to the RPCServer

        Note: this functions DOES return the RPC
        call result although it does not seem it does.
        """

    @rpc_method
    async def not_decorated_method(self, x, y):
        """
        This method is not decorated server-side,
        should not work..
        """


async def main(args):
    rpc_commlayer = await RPCRedisCommLayer.create(
            subchannel=b'sub', pubchannel=b'pub',
            host=args.redis_host, serialization=msgpack_serialization)

    rpc_client = RPCClient(rpc_commlayer)

    service_client = ServiceClient(rpc_client, 'TEST')

    result = await service_client.multiply(100, 100)

    print(result)

    try:
        await service_client.not_decorated_method(100, 100)
    except AttributeError as e:
        print(e)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('redis_host', metavar='H', type=str,
                        help='Redis host IP address')
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(args))