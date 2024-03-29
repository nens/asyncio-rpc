import asyncio
from argparse import ArgumentParser

from asyncio_rpc.commlayers.redis import RPCRedisCommLayer
from asyncio_rpc.serialization import msgpack as msgpack_serialization
from asyncio_rpc.server import DefaultExecutor, RPCServer

# Create a stacked object structure..
#  res = Service().integer.multiply(100, 100)


class Integer:
    """
    Server side implementation for Integer multiplication
    """

    def multiply(self, x, y):
        return x * y


class Service:
    @property
    def integer(self):
        """
        Expose Integer via a property (just like the client side)
        """
        return Integer()


async def main(args):
    rpc_commlayer = await RPCRedisCommLayer.create(
        subchannel=b"pub",
        pubchannel=b"sub",  # Inverse of client
        host=args.redis_host,
        serialization=msgpack_serialization,
    )

    rpc_server = RPCServer(rpc_commlayer)

    # Register the Service above with the the default executor in
    # the TEST namespace
    executor = DefaultExecutor(namespace="TEST", instance=Service())

    # Register executor
    rpc_server.register(executor)

    print("Start serving")
    await rpc_server.serve()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "redis_host", metavar="H", type=str, help="Redis host IP address"
    )
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(args))
