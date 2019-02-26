from asyncio_rpc.models import RPCBase
from abc import ABC, abstractmethod


class AbstractRPCCommLayer(ABC):
    @abstractmethod
    async def publish(self, rpc_model: RPCBase):
        pass  # pragma: nocover

    @abstractmethod
    async def do_subscribe(self):
        pass  # pragma: nocover

    @abstractmethod
    async def subscribe(self, on_rpc_event_callback: callable):
        pass  # pragma: nocover

    @abstractmethod
    async def unsubscribe(self):
        pass  # pragma: nocover
