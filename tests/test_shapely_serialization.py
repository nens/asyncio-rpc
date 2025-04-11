from dataclasses import dataclass

import pytest
from shapely.geometry import (
    GeometryCollection,
    LinearRing,
    LineString,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
)

from asyncio_rpc.serialization import msgpack as msgpack_serialization

# Skip tests if shapely is not installed
shapely = pytest.importorskip("shapely")


def test_point_serialization(serialize_deserialize):
    """Test serialization of Point geometries"""
    value = Point(1.0, 2.0)
    deserialized = serialize_deserialize(value)
    assert value.equals(deserialized)
    assert isinstance(value, type(deserialized))


def test_point_with_z_serialization(serialize_deserialize):
    """Test serialization of 3D Point geometries"""
    value = Point(1.0, 2.0, 3.0)
    deserialized = serialize_deserialize(value)
    assert value.equals(deserialized)
    assert value.has_z == deserialized.has_z
    assert value.z == deserialized.z


def test_linestring_serialization(serialize_deserialize):
    """Test serialization of LineString geometries"""
    value = LineString([(0, 0), (1, 1), (2, 2)])
    deserialized = serialize_deserialize(value)
    assert value.equals(deserialized)
    assert isinstance(value, type(deserialized))
    assert len(value.coords) == len(deserialized.coords)


def test_linearring_serialization(serialize_deserialize):
    """Test serialization of LinearRing geometries"""
    value = LinearRing([(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)])
    deserialized = serialize_deserialize(value)
    assert value.equals(deserialized)
    assert isinstance(value, type(deserialized))
    assert len(value.coords) == len(deserialized.coords)


def test_polygon_serialization(serialize_deserialize):
    """Test serialization of Polygon geometries"""
    # Polygon with exterior only
    value = Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])
    deserialized = serialize_deserialize(value)
    assert value.equals(deserialized)
    assert isinstance(value, type(deserialized))

    # Polygon with interior (hole)
    value = Polygon(
        [(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)],
        [[(2, 2), (2, 8), (8, 8), (8, 2), (2, 2)]],
    )
    deserialized = serialize_deserialize(value)
    assert value.equals(deserialized)
    assert len(value.interiors) == len(deserialized.interiors)


def test_multipoint_serialization(serialize_deserialize):
    """Test serialization of MultiPoint geometries"""
    value = MultiPoint([(0, 0), (1, 1), (2, 2)])
    deserialized = serialize_deserialize(value)
    assert value.equals(deserialized)
    assert isinstance(value, type(deserialized))
    assert len(value.geoms) == len(deserialized.geoms)


def test_multilinestring_serialization(serialize_deserialize):
    """Test serialization of MultiLineString geometries"""
    value = MultiLineString([[(0, 0), (1, 1)], [(2, 2), (3, 3)]])
    deserialized = serialize_deserialize(value)
    assert value.equals(deserialized)
    assert isinstance(value, type(deserialized))
    assert len(value.geoms) == len(deserialized.geoms)


def test_multipolygon_serialization(serialize_deserialize):
    """Test serialization of MultiPolygon geometries"""
    value = MultiPolygon(
        [
            Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]),
            Polygon([(2, 2), (3, 2), (3, 3), (2, 3), (2, 2)]),
        ]
    )
    deserialized = serialize_deserialize(value)
    assert value.equals(deserialized)
    assert isinstance(value, type(deserialized))
    assert len(value.geoms) == len(deserialized.geoms)


def test_geometry_collection_serialization(serialize_deserialize):
    """Test serialization of GeometryCollection"""
    value = GeometryCollection(
        [
            Point(0, 0),
            LineString([(0, 0), (1, 1)]),
            Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]),
        ]
    )
    deserialized = serialize_deserialize(value)
    assert value.equals(deserialized)
    assert isinstance(value, type(deserialized))
    assert len(value.geoms) == len(deserialized.geoms)


@dataclass
class GeometryDataclass:
    id: int
    point: Point
    line: LineString
    polygon: Polygon


# Register the dataclass for serialization
msgpack_serialization.register(GeometryDataclass)


def test_dataclass_with_geometries(serialize_deserialize):
    """Test serialization of dataclass containing geometries"""
    value = GeometryDataclass(
        id=42,
        point=Point(1, 2),
        line=LineString([(0, 0), (1, 1)]),
        polygon=Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]),
    )
    deserialized = serialize_deserialize(value)

    assert value.id == deserialized.id
    assert value.point.equals(deserialized.point)
    assert value.line.equals(deserialized.line)
    assert value.polygon.equals(deserialized.polygon)


def test_list_of_geometries(serialize_deserialize):
    """Test serialization of a list containing different geometry types"""
    value = [
        Point(1, 2),
        LineString([(0, 0), (1, 1)]),
        Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]),
    ]
    deserialized = serialize_deserialize(value)

    assert len(value) == len(deserialized)
    for orig, des in zip(value, deserialized):
        assert orig.equals(des)
        assert type(orig) is type(des)


def test_dict_of_geometries(serialize_deserialize):
    """Test serialization of a dictionary containing geometry values"""
    value = {
        "point": Point(1, 2),
        "line": LineString([(0, 0), (1, 1)]),
        "polygon": Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]),
    }
    deserialized = serialize_deserialize(value)

    assert len(value) == len(deserialized)
    for key in value:
        assert value[key].equals(deserialized[key])
        assert type(value[key]) is type(deserialized[key])
