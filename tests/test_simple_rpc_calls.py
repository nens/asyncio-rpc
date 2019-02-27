import pytest
from dataclasses import dataclass
from uuid import uuid4


from tests.utils import (
    do_rpc_call as do_rpc_call_fixture
)

from asyncio_rpc.models import RPCCall, RPCStack
from asyncio_rpc.client import WrappedException
from asyncio_rpc.server import DefaultExecutor


do_rpc_call = do_rpc_call_fixture


@dataclass
class CustomDataModel:
    x: int
    y: int

    def multiply(self):
        return self.x * self.y


class CustomException(Exception):
    pass


class Service(object):
    """
    Testing service that is register via the TestExecutor
    on the RPCServer
    """

    def __init__(self):
        self._data = {'foo': 'bar'}

    def multiply(self, x, y=1):
        return x * y

    @property
    def data(self):
        return self._data

    def get_item(self, key):
        return self._data[key]

    def custom_error(self):
        raise CustomException("Foobar")

    def multiply_with_dataclass(self, x: CustomDataModel):
        assert isinstance(x, CustomDataModel)
        return x.multiply()


class ServiceClient(object):
    """
    TestService client, exposing (rpc) functions
    that can be called on the TestService instance.
    """
    def __init__(self, client):
        self.client = client

    @property
    async def data(self):
        rpc_func_call = RPCCall('data', [], {})
        rpc_func_stack = RPCStack(
            uuid4().hex, 'TEST', 300, [rpc_func_call])
        return await self.client.rpc_call(rpc_func_stack)

    async def multiply(self, x, y=100):
        rpc_func_call = RPCCall('multiply', [x], {'y': y})
        rpc_func_stack = RPCStack(
            uuid4().hex, 'TEST', 300, [rpc_func_call])
        return await self.client.rpc_call(rpc_func_stack)

    async def get_item(self, key):
        rpc_func_call = RPCCall('get_item', [key], {})
        rpc_func_stack = RPCStack(
            uuid4().hex, 'TEST', 300, [rpc_func_call])
        return await self.client.rpc_call(rpc_func_stack)

    async def custom_error(self):
        rpc_func_call = RPCCall('custom_error', [], {})
        rpc_func_stack = RPCStack(
            uuid4().hex, 'TEST', 300, [rpc_func_call])
        return await self.client.rpc_call(rpc_func_stack)

    async def multiply_with_dataclass(self, x: CustomDataModel):
        assert isinstance(x, CustomDataModel)
        rpc_func_call = RPCCall('multiply_with_dataclass', [x], {})
        rpc_func_stack = RPCStack(
            uuid4().hex, 'TEST', 300, [rpc_func_call])
        return await self.client.rpc_call(rpc_func_stack)


@pytest.mark.asyncio
async def test_simple_call(do_rpc_call):
    test_service_client = ServiceClient(None)
    result = await do_rpc_call(
        test_service_client,
        DefaultExecutor("TEST", Service()),
        test_service_client.multiply(100, 100))
    assert result == 100 * 100


@pytest.mark.asyncio
async def test_simple_call_with_client_processing(do_rpc_call):
    test_service_client = ServiceClient(None)
    result = await do_rpc_call(
        test_service_client,
        DefaultExecutor("TEST", Service()),
        test_service_client.multiply(100, 100),
        client_processing=True)
    assert result == 100 * 100


@pytest.mark.asyncio
async def test_simple_call2(do_rpc_call):
    test_service_client = ServiceClient(None)
    result = await do_rpc_call(
        test_service_client,
        DefaultExecutor("TEST", Service()),
        test_service_client.get_item('foo'))
    assert result == 'bar'


@pytest.mark.asyncio
async def test_property(do_rpc_call):
    test_service_client = ServiceClient(None)
    result = await do_rpc_call(
        test_service_client,
        DefaultExecutor("TEST", Service()),
        test_service_client.data)
    assert result == {'foo': 'bar'}


@pytest.mark.asyncio
async def test_key_error(do_rpc_call):
    test_service_client = ServiceClient(None)
    with pytest.raises(KeyError):
        await do_rpc_call(
            test_service_client,
            DefaultExecutor("TEST", Service()),
            test_service_client.get_item('bar'))


@pytest.mark.asyncio
async def test_not_builtin_exception(do_rpc_call):
    test_service_client = ServiceClient(None)
    with pytest.raises(WrappedException):
        await do_rpc_call(
            test_service_client,
            DefaultExecutor("TEST", Service()),
            test_service_client.custom_error())


@pytest.mark.asyncio
async def test_custom_data_model(do_rpc_call):
    test_service_client = ServiceClient(None)
    value = CustomDataModel(100, 100)
    result = await do_rpc_call(
            test_service_client,
            DefaultExecutor("TEST", Service()),
            test_service_client.multiply_with_dataclass(value),
            custom_dataclasses=[CustomDataModel])
    assert result == value.multiply()
