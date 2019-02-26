import asyncio
import builtins
from .models import RPCMessage, RPCResult, RPCException
from asyncio_rpc.commlayers.base import AbstractRPCCommLayer


class WrappedException(Exception):
    pass


class RPCClient(object):
    def __init__(self, rpc_commlayer: AbstractRPCCommLayer = None):
        assert isinstance(rpc_commlayer, AbstractRPCCommLayer)
        self.rpc_commlayer = rpc_commlayer
        self.futures = {}
        self.queue = asyncio.Queue()
        self.processing = False
        self.on_rpc_message = None

    def register_models(self, models):
        # Register all models
        for model in models:
            self.rpc_commlayer.serialization.register(model)

    async def _wait_for_result(self, uid):
        result = None
        while True:
            item = await self.queue.get()
            # Discard everything that we don't need...
            event, channel = item
            if isinstance(event, RPCResult) or isinstance(event, RPCException):
                if event.uid == uid:
                    result = event
                    break

        # Stop subscription
        await self.rpc_commlayer.unsubscribe()

        return result

    async def rpc_call(self, rpc_func_stack):
        # Make sure to be subscribed
        await self.rpc_commlayer.do_subscribe()

        # Publish message
        count = await self.rpc_commlayer.publish(
            rpc_func_stack)

        # TODO: resent when no subscribers?
        assert count > 0

        if self.processing:
            # TODO: catch timeout exception
            future = asyncio.get_event_loop().create_future()
            self.futures[rpc_func_stack.uid] = future
            result = await asyncio.wait_for(
                future, timeout=rpc_func_stack.timeout)
        else:
            # No background processing, so start the subscription
            # and wait for result via asyncio.gather
            _, result = await asyncio.gather(
                self.rpc_commlayer.subscribe(self._on_rpc_event),
                self._wait_for_result(rpc_func_stack.uid)
            )

        if isinstance(result, RPCException):
            # Try to resolve builtin errors
            try:
                exception_class = getattr(builtins, result.classname)
            except AttributeError:
                # Default to WrappedException
                exception_class = WrappedException

            raise exception_class(*result.exc_args)

        return result.data

    async def _on_rpc_event(self, rpc_instance, channel=None):
        # Put everything in a queue and process
        # it afterwards
        await self.queue.put((rpc_instance, channel))

    async def _process_queue(self, on_rpc_message=None):
        self.processing = True

        while True:
            item = await self.queue.get()
            if item == b'END':
                break

            event, channel = item
            if isinstance(event, RPCResult) or isinstance(event, RPCException):
                if event.uid in self.futures:
                    future = self.futures.pop(event.uid)
                    if future is not None:
                        future.set_result(event)
                else:
                    # print("FUTURE NOT FOUND FOR", event)
                    pass  # pragma: nocover
            elif isinstance(event, RPCMessage) and on_rpc_message:
                await on_rpc_message(event, channel)

        self.processing = False

    async def serve(self, on_rpc_message=None):
        """
        Wait and process incoming messages...
        """
        await asyncio.gather(
            self.rpc_commlayer.subscribe(self._on_rpc_event),
            self._process_queue(on_rpc_message))

#    async def rpc_call_stack(self, func_calls_stack, namespace=None):
#        assert namespace is not None
#        rpc_func_stack = RPCStack(
#            uuid4().hex, namespace, RESULT_EXPIRE_TIME, [])
#
#        for func_name, func_args, func_kwargs in func_calls_stack:
#            rpc_func_stack.stack.append(
#                RPCCall(func_name, func_args, func_kwargs))
#
#        return await self.rpc_call(rpc_func_stack)
