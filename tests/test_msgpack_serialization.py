import pytest
import numpy as np
import datetime
from dataclasses import dataclass
from asyncio_rpc.serialization import msgpack as msgpack_serialization


@pytest.fixture()
def serialize_deserialize():
    def func(value):
        return msgpack_serialization.loadb(
            msgpack_serialization.dumpb(value))
    return func


def test_dict_serialization(serialize_deserialize):
    value = {'1': 2, 10: 1.10}
    assert value == serialize_deserialize(value)


def test_numpy_serialization(serialize_deserialize):
    value = np.arange(100, dtype=np.float64)
    assert np.all(value == serialize_deserialize(value))


def test_datetime_serialization(serialize_deserialize):
    value = datetime.datetime.now()
    assert value == serialize_deserialize(value)


def test_none_serialization(serialize_deserialize):
    assert serialize_deserialize(None) is None


def test_none_deserialization():
    assert msgpack_serialization.loadb(None) is None


@dataclass
class DataclassTest:
    uid: int
    data: np.ndarray


msgpack_serialization.register(DataclassTest)


def test_dataclass_serialization(serialize_deserialize):
    value = DataclassTest(101, np.arange(100, dtype=np.float32))
    deserialized = serialize_deserialize(value)
    assert value.uid == deserialized.uid
    assert np.all(value.data == serialize_deserialize(value).data)


@dataclass
class UnregisteredTest:
    uid: int
    data: np.ndarray


def test_unregistered_serialization(serialize_deserialize):
    value = UnregisteredTest(101, np.arange(100, dtype=np.float32))
    with pytest.raises(TypeError):
        serialize_deserialize(value)
