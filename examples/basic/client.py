import asyncio
from uuid import uuid4
from argparse import ArgumentParser
from asyncio_rpc.client import RPCClient
from asyncio_rpc.models import RPCCall, RPCStack
from asyncio_rpc.commlayers.redis import RPCRedisCommLayer
from asyncio_rpc.serialization import msgpack as msgpack_serialization


class ServiceClient:
    """
    'Proxy' class exposing the same functions as the
    executor on the server side.
    """

    def __init__(self, client: RPCClient, namespace=None):
        """
        Set the RPC client and the namespace (should be same as server side)
        """
        assert namespace is not None
        assert client is not None
        self.client = client
        self.namespace = namespace

    async def _rpc_call(self, func_name, func_args, func_kwargs):
        """
        Helper function to wrap a Python function call into a RPCCall.

        A RPCCall wraps a function by a function's:
            name: str
            args: List
            kwargs: Dict

        A RPCStack can have multiple RPCCall's. The RPCStack is sent
        to the RPC server.
        """
        rpc_func_call = RPCCall(func_name, func_args, func_kwargs)
        rpc_func_stack = RPCStack(uuid4().hex, self.namespace, 300, [rpc_func_call])

        # Let the client sent the RPCStack to the server.
        # The server executes the function specified
        # by the RPCStack and returns the result to the client.
        # This result is returned by this method.
        return await self.client.rpc_call(rpc_func_stack)

    async def multiply(self, x, y):
        """
        Multiply (proxy) function. This function is executed
        server side and returns the returned result.
        """
        return await self._rpc_call(
            func_name="multiply", func_args=[x, y], func_kwargs={}
        )


async def main(args):
    """
    The RPC client (and server) need a communicationlayer to communicate.
    Below the default Redis implementation is used together with the
    default msgpack serialization.
    """
    rpc_commlayer = await RPCRedisCommLayer.create(
        subchannel=b"sub",
        pubchannel=b"pub",
        host=args.redis_host,
        serialization=msgpack_serialization,
    )

    # Create a nwe RPCClient with the defined commlayer
    rpc_client = RPCClient(rpc_commlayer)

    # Create a ServiceClient which is a proxy class exposing
    # the same methods as available server side in the executor.
    service_client = ServiceClient(rpc_client, "TEST")

    # Execute the multiply function via RPC
    result = await service_client.multiply(100, 100)

    print(result)


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
