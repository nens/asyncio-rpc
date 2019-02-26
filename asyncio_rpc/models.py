from dataclasses import dataclass
from typing import List, Dict, Any


class RPCBase:
    """
    Baseclass to identify all RPC dataclasses
    """


@dataclass
class RPCMessage(RPCBase):
    """
    Message definition. Can be used to publish some data

    :param uid: the unique id for this RPC message
    :param namespace: the namespace
    :param data: the data to sent (should not be to much data!)
    """
    uid: str
    namespace: str
    data: Any


@dataclass
class RPCCall(RPCBase):
    """
    Remote procedure call definition

    :param name: the name of the function to execute
    :param args: args for the function
    :param kwargs: kwargs for the function
    """
    func_name: str
    func_args: List
    func_kwargs: Dict


@dataclass
class RPCStack(RPCBase):
    """
    Represents a remote Procedure function call stack, for example the
    call:
        gr.nodes.subset('2D_open_water').filter(id__lt=100).reproject_to('4326').coordinates

    Would procedure the following stack:
        [
            RPCCall('nodes', [], {}),
            RPCCall('subset',['2D_open_water'], {}),
            RPCCall('filter',[], {'id__lt': 100}),
            RPCCall('reproject_to',['4326'], {}),
            RPCCall('coordinates', [], {}),
        ]

    Note: properties are also encoded as function calls.
    """
    uid: str
    namespace: str
    timeout: float
    stack: List[RPCCall]
    respond_to: str = None


@dataclass
class RPCResult(RPCBase):
    """
    Represents the result of a remote procedure call (RPCStack)

    :param uid: is set to RPCStack.uid
    :param namespace: is set to RPCStack.namespace
    :param data: is the result of the RPCStack call
    """
    uid: str
    namespace: str
    data: Any


@dataclass
class RPCException(RPCBase):
    """
    Represents an exception raised during executing the remote procedure
    call server-side

    :param uid: is set to RPCStack.uid
    :param namespace: is set to RPCStack.namespace
    :param classname: the classname of the exception raised
    :param exc_args: the exception args as a list
    """
    uid: str
    namespace: str
    classname: str
    exc_args: List


# List of serializable model to
# register in the serialization
SERIALIZABLE_MODELS = (
    RPCMessage,
    RPCCall,
    RPCStack,
    RPCResult,
    RPCException
)
