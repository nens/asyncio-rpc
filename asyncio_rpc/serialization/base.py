from abc import ABC, abstractmethod
from typing import Any


class AbstractHandler(ABC):
    ext_type: int = None  # Unique int
    obj_type: Any = None  # Unique object type

    @classmethod
    @abstractmethod
    def packb(cls, instance: Any) -> bytes:
        """
        Pack the instance into bytes
        """

    @classmethod
    @abstractmethod
    def unpackb(cls, data: bytes) -> Any:
        """
        Unpack the data back into an instance
        """
