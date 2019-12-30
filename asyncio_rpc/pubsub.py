import asyncio
import builtins
from typing import Any, AsyncIterator
from asyncio_rpc.models import (
    RPCStack, RPCPubResult, RPCException, RPCUnSubStack)
from asyncio_rpc.exceptions import WrappedException


class Publisher:
    def __init__(self, server, rpc_stack: RPCStack):
        self._rpc_stack = rpc_stack
        self._server = server
        self._is_active = True

    def set_is_active(self, is_active: bool):
        self._is_active = is_active

    @property
    def is_active(self):
        return self._is_active

    @property
    def rpc_stack(self):
        return self._rpc_stack

    async def publish(self, data: Any):
        """
        Publish data to the client
        """
        if not self.is_active:
            return 0

        # Publish the data as partial data
        publication = RPCPubResult(
            self._rpc_stack.uid, self._rpc_stack.namespace, data)
        receiver_count = await self._server.rpc_commlayer.publish(
            publication, channel=self._rpc_stack.respond_to)

        if receiver_count == 0:
            self._is_active = False
            self._server.publishers.pop(self._rpc_stack.uid, None)
            return 0

        return receiver_count

    def __del__(self):
        self._server.publishers.pop(self._rpc_stack.uid, None)


class Subscription:
    def __init__(self, client, rpc_stack: RPCStack):
        self.queue = asyncio.Queue()
        self._client = client
        self._rpc_stack = rpc_stack

    async def enqueue(self, data: Any):
        await self.queue.put(data)

    async def close(self):
        self._client.subscriptions.pop(self._rpc_stack.uid, None)

        rpc_unsub_stack = RPCUnSubStack(
            self._rpc_stack.uid, self._rpc_stack.namespace,
            300, [None])

        # Publish to RPCServer
        await self._client.rpc_commlayer.publish(
            rpc_unsub_stack)

        self.queue._queue.clear()
        self.queue._finished.set()
        self.queue._unfinished_tasks = 0
        await self.queue.put(b'STOP')

    async def enumerate(self) -> AsyncIterator[Any]:
        while True:
            result = await self.queue.get()
            if result == b'STOP':
                break

            if isinstance(result, RPCException):
                # Try to resolve builtin errors
                try:
                    exception_class = getattr(builtins, result.classname)
                except AttributeError:
                    # Default to WrappedException if
                    # returned exception is not a builtin error
                    exception_class = WrappedException

                raise exception_class(*result.exc_args)

            yield result.data

    def __del__(self):
        self._client.subscriptions.pop(
            self._rpc_stack.uid, None)
