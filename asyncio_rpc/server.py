import asyncio
from typing import List
from asyncio_rpc.models import RPCStack, RPCResult, RPCException, RPCCall
from asyncio_rpc.commlayers.base import AbstractRPCCommLayer


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

            # Process rpc_func_call_stack
            result = await self.rpc_call(rpc_func_stack)

            # Publish result of rpc call
            await self.rpc_commlayer.publish(
                result, channel=rpc_func_stack.respond_to)

    async def serve(self):
        """
        Main entry point for RPCServer.

        Starts RPCServer background processing, blocks
        until self.rpc_commlayer.unsubscribe() is called.
        """
        await asyncio.gather(
            self.rpc_commlayer.subscribe(self._on_rpc_event),
            self._process_queue()
        )


class DefaultExecutor:
    """
    Default executor implementation, override if necessary
    """

    def __init__(self, namespace, instance):
        assert namespace is not None
        assert instance is not None
        self.namespace = namespace
        self.instance = instance

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
