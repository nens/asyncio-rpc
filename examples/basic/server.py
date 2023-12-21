import asyncio
from argparse import ArgumentParser

from asyncio_rpc.commlayers.redis import RPCRedisCommLayer
from asyncio_rpc.serialization import msgpack as msgpack_serialization
from asyncio_rpc.server import DefaultExecutor, RPCServer


class Service:
    """
    Class holding the real multiply function.
    This function is executed by the RPC Server via
    the DefaultExecutor.
    """

    def multiply(self, x, y):
        return x * y


async def main(args):
    """
    The RPC client (and server) need a communicationlayer to communicate.
    Below the default Redis implementation is used together with the
    default msgpack serialization.
    """
    rpc_commlayer = await RPCRedisCommLayer.create(
        subchannel=b"pub",
        pubchannel=b"sub",  # Inverse of client
        host=args.redis_host,
        serialization=msgpack_serialization,
    )

    # Create a RPC Server with the commlayer
    rpc_server = RPCServer(rpc_commlayer)

    # Register the Service above with the default executor in
    # the TEST namespace
    #
    # The executor receives a RPCStack from the commlayer
    # and will try to execute the provided function names (with
    # args & kwargs)
    executor = DefaultExecutor(namespace="TEST", instance=Service())

    # Register executor.
    rpc_server.register(executor)

    print("Start serving")
    await rpc_server.serve()


if __name__ == "__main__":
    parser = ArgumentParser()

    # Provide Redis host that is accessible for both client/server.
    parser.add_argument(
        "redis_host", metavar="H", type=str, help="Redis host IP address"
    )
    args = parser.parse_args()

    # Create asyncio loop and execute main method
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(args))
