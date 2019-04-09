import asyncio
from argparse import ArgumentParser
from asyncio_rpc.server import RPCServer, DefaultExecutor
from asyncio_rpc.commlayers.redis import RPCRedisCommLayer
from asyncio_rpc.serialization import msgpack as msgpack_serialization
from .models import Integer, MultiplyResult


class Service:
    """
    Same service as the basic example, only now it uses
    dataclasses as arguments and returns a dataclass with
    the result.
    """
    def multiply(self, x: Integer, y: Integer) -> MultiplyResult:
        return MultiplyResult(x.value * y.value)


async def main(args):
    rpc_commlayer = await RPCRedisCommLayer.create(
            subchannel=b'pub', pubchannel=b'sub',  # Inverse of client
            host=args.redis_host, serialization=msgpack_serialization)

    rpc_server = RPCServer(rpc_commlayer)

    # Register the Service above with the the default executor in
    # the TEST namespace
    executor = DefaultExecutor(
        namespace="TEST", instance=Service())

    # IMPORTANT: Register dataclasses to allow serialization/deserialization
    rpc_server.register_models([Integer, MultiplyResult])

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
