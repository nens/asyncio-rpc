import asyncio
from typing import List
from argparse import ArgumentParser
from asyncio_rpc.server import RPCServer, DefaultExecutor
from asyncio_rpc.models import RPCCall
from asyncio_rpc.commlayers.redis import RPCRedisCommLayer
from asyncio_rpc.serialization import msgpack as msgpack_serialization


def rpc_method(func):
    def rpc_method(*args, **kwargs):
        return func(*args, **kwargs)
    rpc_method._is_rpc_method = True
    return rpc_method


class Service:
    @rpc_method
    def multiply(self, x, y):
        return x * y

    def not_decorated_method(self, x, y):
        return x * y


class DecoratorFilterExecutor(DefaultExecutor):
    async def rpc_call(self, stack: List[RPCCall] = []):
        """
        Process incoming rpc call stack.
        The stack can contain multiple chained function calls for example:
            node.filter(id=1).reproject_to('4326').data
        """

        resource = self.instance

        for rpc_func_call in stack:
            assert isinstance(rpc_func_call, RPCCall)

            # Try to get the function/property from self.instance
            instance_attr = getattr(resource, rpc_func_call.func_name)

            if not hasattr(instance_attr, '_is_rpc_method'):
                raise AttributeError(
                    "%s is not a RPC method" % rpc_func_call.func_name)

            if callable(instance_attr):
                # Function
                resource = instance_attr(
                    *rpc_func_call.func_args,
                    **rpc_func_call.func_kwargs)
            else:
                # Asume property
                resource = instance_attr

        return resource


async def main(args):
    rpc_commlayer = await RPCRedisCommLayer.create(
            subchannel=b'pub', pubchannel=b'sub',  # Inverse of client
            host=args.redis_host, serialization=msgpack_serialization)

    rpc_server = RPCServer(rpc_commlayer)

    # Register the Service above with the the default executor in
    # the TEST namespace
    executor = DecoratorFilterExecutor(
        namespace="TEST", instance=Service())

    # Register executor
    rpc_server.register(executor)

    print('Start serving')
    await rpc_server.serve()

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('redis_host', metavar='H', type=str,
                        help='Redis host IP address')
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(args))
