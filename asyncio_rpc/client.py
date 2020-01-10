import asyncio
import builtins
import logging
from typing import Union, List
from .models import (
    RPCMessage, RPCResult, RPCException, RPCStack, RPCBase, RPCSubStack)
from asyncio_rpc.commlayers.base import AbstractRPCCommLayer
from asyncio_rpc.pubsub import Subscription
from asyncio_rpc.exceptions import (
    RPCTimeoutError, WrappedException, NotReceived)

logger = logging.getLogger("asyncio-rpc-client")


class RPCClient(object):
    """
    Remote procedure client class. Allows to send rpc_call
    to a RPCServer via a rpc_commlayer.
    """

    def __init__(self, rpc_commlayer: AbstractRPCCommLayer):
        """
        Initialize a new RPCClient by providing an implementation of
        AbstractRPCCommlayer
        """
        assert isinstance(rpc_commlayer, AbstractRPCCommLayer)
        self.rpc_commlayer = rpc_commlayer
        self.futures = {}
        self.queue = asyncio.Queue()
        self.processing = False
        self.on_rpc_message = None
        self.subscriptions = {}

    def register_models(self, models: List):
        """
        Register all given models to the rpc_commlayer serialization

        Intended usage is to register dataclasses
        """
        for model in models:
            self.rpc_commlayer.serialization.register(model)

    async def _wait_for_result(
            self, uid: bytes) -> Union[RPCResult, RPCException]:
        """
        Internal helper function for stopping the rpc_commlayer subscription
        upon receiving a result from the RPC_server
        """
        result = None
        while True:
            event, channel = await self.queue.get()

            assert isinstance(event, RPCResult) or\
                isinstance(event, RPCException)

            # Discard everything that we don't need...
            if event.uid == uid:
                result = event
                break

        # Stop subscription, automatically stops
        # queue processing as well
        await self.rpc_commlayer.unsubscribe()

        return result

    async def subscribe_call(
            self, rpc_sub_stack: RPCSubStack, channel=None) -> Subscription:
        assert isinstance(rpc_sub_stack, RPCStack)

        if not self.processing:
            pass

        # Make sure to be subscribed before publishing
        await self.rpc_commlayer.do_subscribe()

        subscription = Subscription(self, rpc_sub_stack)

        self.subscriptions[rpc_sub_stack.uid] = subscription

        # Publish RPCStack to RPCServer
        count = await self.rpc_commlayer.publish(
            rpc_sub_stack, channel=channel)

        if count == 0:
            raise NotReceived(
                f"subscribe_call was not "
                f"received by any server: {rpc_sub_stack}")

        return subscription

    async def rpc_call(
            self, rpc_func_stack: RPCStack, channel=None) -> RPCResult:
        """
        Execute the given rpc_func_stack (RPCStack) and either
        return a RPCResult or raise an exception based on the returned
        RPCException.

        This function can both be called with awaiting client.serve() or
        without. The difference is, that in the first case client.serve()
        starts while loops for performing background processing.

        The channel (optional) argument can be used to override
        the default publish channel
        """
        assert isinstance(rpc_func_stack, RPCStack)

        # Make sure to be subscribed before publishing
        await self.rpc_commlayer.do_subscribe()

        # Publish RPCStack to RPCServer
        count = await self.rpc_commlayer.publish(
            rpc_func_stack, channel=channel)

        if count == 0:
            raise NotReceived(
                f"rpc_call was not received "
                f"by any subscriber {rpc_func_stack}")

        if self.processing:
            # client.serve() has been awaited, so
            # background processing is taken care of.

            # Create a future that should be resolved within
            # the given timeout. The background processing initialized
            # by client.serve() resolves the future when a result
            # is returned.
            future = asyncio.get_event_loop().create_future()
            self.futures[rpc_func_stack.uid] = future
            try:
                result = await asyncio.wait_for(
                    future, timeout=rpc_func_stack.timeout)
            except asyncio.TimeoutError:
                raise RPCTimeoutError(f"rpc_func_stack: {rpc_func_stack}")
        else:
            # No background processing, so start the subscription
            # and wait for result via asyncio.gather
            # _wait_for_result is a helper function to unsubscribe
            # on a result.
            try:
                _, result = await asyncio.gather(
                    self.rpc_commlayer.subscribe(self._on_rpc_event),
                    self._wait_for_result(rpc_func_stack.uid)
                )
            except asyncio.TimeoutError:
                raise RPCTimeoutError(f"rpc_func_stack: {rpc_func_stack}")

        if isinstance(result, RPCException):
            # Try to resolve builtin errors
            try:
                exception_class = getattr(builtins, result.classname)
            except AttributeError:
                # Default to WrappedException if
                # returned exception is not a builtin error
                exception_class = WrappedException

            raise exception_class(*result.exc_args)

        return result.data

    async def _on_rpc_event(
            self, rpc_instance: RPCBase, channel: bytes = None):
        """
        Callback function sent to rpc_commlayer, is called
        when a message is received by the subscription.
        """
        assert isinstance(rpc_instance, RPCBase)
        # Put everything in a queue and process
        # it afterwards
        await self.queue.put((rpc_instance, channel))

    async def _process_queue(self, on_rpc_message: callable = None):
        """
        Background queue processing function, processes
        the internal self.queue until b'END' is received


        if on_rpc_message has been set, it will be called
        whenever a RPCMessage is popped from the queue.
        """
        self.processing = True

        while True:
            item = await self.queue.get()
            if item == b'END':
                break

            event, channel = item
            # The event can either be a:
            # 1) RPCResult or RPCException as a result from the RPCServer
            # 3) RPCMessage as a message from the RPCServer
            assert isinstance(event, RPCResult) or\
                isinstance(event, RPCException) or\
                isinstance(event, RPCMessage)

            if isinstance(event, RPCResult) or isinstance(event, RPCException):
                if event.uid in self.futures:
                    # A future is created & awaited in self.rpc_call
                    # resolve this future to proceed in the rpc_call function
                    # and return a result
                    future = self.futures.pop(event.uid)
                    if future is not None:
                        future.set_result(event)
                elif event.uid in self.subscriptions:
                    subscription = self.subscriptions[event.uid]
                    await subscription.enqueue(event)
                else:
                    # FUTURE NOT FOUND FOR EVENT
                    # TODO: how to handle this??
                    pass  # pragma: nocover
            elif isinstance(event, RPCMessage) and on_rpc_message:
                await on_rpc_message(event, channel)

        self.processing = False

    async def serve(self, on_rpc_message=None):
        """
        Start RPCClient background processing, blocks
        until self.rpc_commlayer.unsubscribe() is called.

        Use this method in an async context to enable
        background processing and allowing multiple
        rpc_calls asynchroniously.
        """

        task_args_map = {
            self.rpc_commlayer.subscribe: [self._on_rpc_event],
            self._process_queue: [on_rpc_message]
        }
        # create the main tasks
        main_tasks = {
            asyncio.ensure_future(coro(*args)): (coro, args)
            for coro, args in task_args_map.items()
        }

        running = set(main_tasks.keys())

        except_cnt = -1

        while running:
            except_cnt += 1
            finished, running = await asyncio.wait(
                running, return_when=asyncio.FIRST_EXCEPTION
            )
            for task in finished:
                if task.exception():
                    logger.exception(task.exception())
                    task.print_stack()
                    coro, args = main_tasks[task]
                    new_task = asyncio.ensure_future(coro(*args))
                    main_tasks[new_task] = (coro, args)
                    running.add(new_task)
