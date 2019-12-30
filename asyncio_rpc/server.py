import asyncio
import logging
from typing import List
from asyncio_rpc.models import (
    RPCStack, RPCResult, RPCException, RPCCall,
    RPCSubStack, RPCUnSubStack)
from asyncio_rpc.commlayers.base import AbstractRPCCommLayer
from asyncio_rpc.pubsub import Publisher
logger = logging.getLogger("asyncio-rpc-server")


class NamespaceError(Exception):
    """
    Exception raised when a namespace unknown or
    already present.
    """


class RPCServer(object):
    """
    Remote procedure server class. Allows to register executors
    by namespace and execute RPC calls from a RPCClient
    """
    def __init__(self, rpc_commlayer: AbstractRPCCommLayer = None):
        assert isinstance(rpc_commlayer, AbstractRPCCommLayer)
        self.queue = asyncio.Queue()
        self._alive = True

        # Allow multiple executors to be registered by
        # namespace
        self.registry = {}
        self.publishers = {}
        self.rpc_commlayer = rpc_commlayer

    def register_models(self, models):
        """
        Register all given models to the rpc_commlayer serialization

        Intended usage is to register dataclasses
        """
        for model in models:
            self.rpc_commlayer.serialization.register(model)

    def register(self, executor):
        """
        Register an executor for a namespace, the namespace
        should be unique and is used to route RPC calls from
        the client to the correct executor in the registry of
        the RPCServer.
        """
        assert hasattr(executor, 'namespace')

        if executor.namespace in self.registry:
            raise NamespaceError("Namespace already exists")

        # Register executor for this namespaces
        self.registry[executor.namespace] = executor

    async def rpc_call(self, rpc_func_stack: RPCStack):
        """
        Incoming rpc_call, execute it via the registered
        executor and return the result or exception
        """
        assert isinstance(rpc_func_stack, RPCStack)

        # Create a default result
        result = RPCResult(
            uid=rpc_func_stack.uid,
            namespace=rpc_func_stack.namespace,
            data=None)

        if rpc_func_stack.namespace not in self.registry:
            raise NamespaceError("Unknown namespace")

        executor = self.registry[rpc_func_stack.namespace]

        try:
            # Wait for result from executor
            result.data = await asyncio.wait_for(
                executor.rpc_call(rpc_func_stack.stack),
                timeout=rpc_func_stack.timeout)
        except Exception as e:
            # For now catch all exceptions here...
            # TODO: debug mode with stacktrace
            result = RPCException(
                uid=rpc_func_stack.uid,
                namespace=rpc_func_stack.namespace,
                classname=e.__class__.__name__,
                exc_args=e.args)

        return result

    async def subscribe_call(self, rpc_sub_stack: RPCSubStack):
        assert isinstance(rpc_sub_stack, RPCSubStack)
        if rpc_sub_stack.namespace not in self.registry:
            raise NamespaceError("Unknown namespace")

        executor = self.registry[rpc_sub_stack.namespace]
        if not hasattr(executor, 'subscribe_call'):
            raise NotImplementedError(
                f"Executor for namespace: {rpc_sub_stack.namespace} has "
                f"no subscribe_call function")

        publisher = Publisher(self, rpc_sub_stack)
        self.publishers[rpc_sub_stack.uid] = publisher

        # Create task for this publisher
        asyncio.create_task(
            executor.subscribe_call(publisher))

    async def _on_rpc_event(
            self, rpc_func_stack: RPCStack, channel: bytes = None):
        """
        Callback function sent to rpc_commlayer, is called
        when a RPCStack is received by the rpc_commlayer subscription
        """
        await self.queue.put((rpc_func_stack, channel))

    async def _process_queue(self):
        """
        Background queue processing function, processes
        the internal self.queue until b'END' is received


        if on_rpc_message has been set, it will be called
        whenever a RPCMessage is popped from the queue.
        """

        while self._alive:
            item = await self.queue.get()

            if item == b'END':
                break

            rpc_func_stack, channel = item

            assert isinstance(rpc_func_stack, RPCStack)

            if isinstance(rpc_func_stack, RPCSubStack):
                try:
                    # Process rpc_func_call_stack
                    await self.subscribe_call(rpc_func_stack)
                except Exception as e:
                    result = RPCException(
                        uid=rpc_func_stack.uid,
                        namespace=rpc_func_stack.namespace,
                        classname=e.__class__.__name__,
                        exc_args=e.args)
                    # Publish exception
                    await self.rpc_commlayer.publish(
                        result, channel=rpc_func_stack.respond_to)
            elif isinstance(rpc_func_stack, RPCUnSubStack):
                publisher = self.publishers.pop(rpc_func_stack.uid, None)
                if publisher is not None:
                    publisher.set_is_active(False)
            else:
                try:
                    # Process rpc_func_call_stack
                    result = await self.rpc_call(rpc_func_stack)
                    # Publish result of rpc call
                    await self.rpc_commlayer.publish(
                        result, channel=rpc_func_stack.respond_to)

                except Exception as e:
                    result = RPCException(
                        uid=rpc_func_stack.uid,
                        namespace=rpc_func_stack.namespace,
                        classname=e.__class__.__name__,
                        exc_args=e.args)
                    # Try to publish error
                    await self.rpc_commlayer.publish(
                        result, channel=rpc_func_stack.respond_to)

    async def serve(self):
        """
        Main entry point for RPCServer.

        Starts RPCServer background processing, blocks
        until self.rpc_commlayer.unsubscribe() is called.
        """
        task_args_map = {
            self.rpc_commlayer.subscribe: [self._on_rpc_event],
            self._process_queue: []
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


class DefaultExecutor:
    """
    Default executor implementation, override if necessary
    """

    def __init__(self, namespace, instance):
        assert namespace is not None
        assert instance is not None
        self.namespace = namespace
        self.instance = instance

    async def subscribe_call(self, publisher: Publisher):
        """
        Use the Publisher to publish results to the client
        """
        # if publisher.is_active:
        #     await publisher.publish(b'blaat')
        pass

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

            if callable(instance_attr):
                # Function
                resource = instance_attr(
                    *rpc_func_call.func_args,
                    **rpc_func_call.func_kwargs)
            else:
                # Asume property
                resource = instance_attr

        return resource
