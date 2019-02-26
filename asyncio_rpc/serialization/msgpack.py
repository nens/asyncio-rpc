import msgpack
import numpy as np
from io import BytesIO
from datetime import datetime
import dataclasses
from lz4.frame import compress as lz4_compress, decompress as lz4_decompress


# Maximum byte lengths for str/ext
MAX_STR_LEN = 2147483647
MAX_EXT_LEN = 2147483647

REGISTRY = {'obj_types': {},
            'ext_types': {},
            'serializables': {}}


def str_to_bytes(value, encoding='utf-8'):
    if isinstance(value, str):
        value = value.encode(encoding)
    return value


def register(obj_def):
    if dataclasses.is_dataclass(obj_def):
        class_name = obj_def.__name__
        REGISTRY['serializables'][class_name] = obj_def
        REGISTRY['obj_types'][obj_def] = DataclassHandler

        # Register DataclassHandler if not done already
        if DataclassHandler.ext_type not in REGISTRY['ext_types']:
            REGISTRY['ext_types'][
                DataclassHandler.ext_type] = DataclassHandler
    else:
        REGISTRY['obj_types'][obj_def.obj_type] = obj_def
        REGISTRY['ext_types'][obj_def.ext_type] = obj_def


class NumpyArray:
    """
    Use np.save and np.load to serialize/deserialize
    numpy array's.

    Compress/decompress data with lz4
    """
    ext_type = 1
    obj_type = np.ndarray

    #  More generic approach, but slower..
    @classmethod
    def packb(cls, np_ndarray):
        buf = BytesIO()
        np.save(buf, np_ndarray)
        buf.seek(0)
        return buf.read()

    @classmethod
    def unpackb(cls, bytes_data):
        buf = BytesIO(bytes_data)
        buf.seek(0)
        return np.load(buf)


class NumpyStructuredArray(NumpyArray):
    ext_type = 2
    obj_type = np.void


class Datetime:
    ext_type = 3
    obj_type = datetime

    @classmethod
    def packb(cls, dt):
        return b'%f' % dt.timestamp()

    @classmethod
    def unpackb(cls, bytes_data):
        return datetime.fromtimestamp(float(bytes_data))


class DataclassHandler:
    ext_type = 5

    @classmethod
    def packb(cls, obj):
        return dumpb(
            (str_to_bytes(obj.__class__.__name__), obj.__dict__),
            do_compress=False)

    @classmethod
    def unpackb(cls, bytes_data):
        classname, data = loadb(
            bytes_data, do_decompress=False, raw=False)
        # Return registered class or Serializable (as default)
        assert classname in REGISTRY['serializables']
        klass = REGISTRY['serializables'][classname]
        return klass(**data)


# Register custom types
register(NumpyArray)
register(NumpyStructuredArray)
register(Datetime)


def default(obj):
    if type(obj) in REGISTRY['obj_types']:
        obj_serialization = REGISTRY['obj_types'][type(obj)]
        return msgpack.ExtType(
            obj_serialization.ext_type, obj_serialization.packb(obj))
    raise TypeError("Unknown type: %r" % (obj,))


def ext_hook(ext_type, bytes_data):
    if ext_type in REGISTRY['ext_types']:
        obj_serialization = REGISTRY['ext_types'][ext_type]
        return obj_serialization.unpackb(bytes_data)
    raise TypeError("Unknown ext_type: %r" % (ext_type,))  # pragma: no cover


def dummy(data):
    return data


def dumpb(obj, do_compress=True, compress_func=lz4_compress):
    if not do_compress:
        compress_func = dummy
    return compress_func(msgpack.packb(obj, default=default))


def loadb(packed, do_decompress=True, decompress_func=lz4_decompress,
          raw=False):
    if packed is None:
        return None
    if not do_decompress:
        decompress_func = dummy
    return msgpack.unpackb(
        decompress_func(packed), ext_hook=ext_hook,
        max_ext_len=MAX_EXT_LEN,
        max_str_len=MAX_STR_LEN, raw=raw)
