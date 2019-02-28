from asyncio_rpc.models import RPCBase
from abc import ABC, abstractmethod


class AbstractRPCCommLayer(ABC):
    """
    Abstract baseclass for RPC communication layer
    """
    @abstractmethod
    async def publish(self, rpc_instance: RPCBase):
        """
        Publish a RPCBase subclass to the other end,
        either a RPCServer or RPCClient.
        """

    @abstractmethod
    async def do_subscribe(self):
        """
        Initialize subscription for receiving messages.
        This is needed for Redis to make sure all
        message are received, this might not be the case
        for other communication layers
        """

    @abstractmethod
    async def subscribe(self, on_rpc_event_callback: callable):
        """
        Subscribe and listen for messages. The on_rpc_event_callback
        function is called on every received RPCBase message
        """

    @abstractmethod
    async def unsubscribe(self):
        """
        Stop subscription for receiving messages.
        This is needed for Redis and might not be needed
        for other communication layers
        """
