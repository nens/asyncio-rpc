import asyncio
from asyncio_rpc.models import RPCStack, RPCResult, RPCException
from asyncio_rpc.commlayers.base import AbstractRPCCommLayer


class NamespaceError(Exception):
    pass


class RPCServer(object):
    def __init__(self, rpc_commlayer: AbstractRPCCommLayer = None):
        assert isinstance(rpc_commlayer, AbstractRPCCommLayer)
        self.queue = asyncio.Queue()
        self._alive = True
        self.registry = {}
        self.rpc_commlayer = rpc_commlayer

    def register_models(self, models):
        # Register all models
        for model in models:
            self.rpc_commlayer.serialization.register(model)

    def register(self, executor):
        """
        Register an executor for a namespace
        """

        assert hasattr(executor, 'namespace')

        if executor.namespace in self.registry:
            raise NamespaceError("Namespace already exists")

        # Register executor for this namespaces
        self.registry[executor.namespace] = executor

    async def rpc_call(self, rpc_func_stack=None):
        """
        Incoming rpc_call

        :param rpc_func_stack: instance of RPCFunctionCallStack
        """
        result = RPCResult(
            uid=rpc_func_stack.uid,
            namespace=rpc_func_stack.namespace,
            data=None)

        # rpc_func_calls should all be RPCFunctionCall instances
        if rpc_func_stack.namespace not in self.registry:
            raise NamespaceError("Unknown namespace")

        executor = self.registry[rpc_func_stack.namespace]

        try:
            # Wait for result...
            result.data = await asyncio.wait_for(
                executor.rpc_call(rpc_func_stack.stack),
                timeout=rpc_func_stack.timeout)
        except Exception as e:
            result = RPCException(
                uid=rpc_func_stack.uid,
                namespace=rpc_func_stack.namespace,
                classname=e.__class__.__name__,
                exc_args=e.args)

        return result

    async def _on_rpc_event(self, rpc_func_call_stack, channel=None):
        # Put everything in a queue and process
        # it afterwards
        await self.queue.put((rpc_func_call_stack, channel))

    async def _process_queue(self):
        """
        Main processing loop
        """
        while self._alive:
            item = await self.queue.get()

            if item == b'END':
                break

            rpc_func_call_stack, channel = item
            assert isinstance(rpc_func_call_stack, RPCStack)

            # Process rpc_func_call_stack
            result = await self.rpc_call(rpc_func_call_stack)

            # Publish result of rpc call
            await self.rpc_commlayer.publish(
                result, channel=rpc_func_call_stack.respond_to)

    async def serve(self):
        await asyncio.gather(
            self.rpc_commlayer.subscribe(self._on_rpc_event),
            self._process_queue()
        )
