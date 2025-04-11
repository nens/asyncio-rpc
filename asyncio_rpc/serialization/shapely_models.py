try:
    import shapely as shp
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
    from shapely.geometry.base import BaseGeometry
    from shapely.wkb import dumps, loads

    from asyncio_rpc.serialization.base import AbstractHandler
except ImportError:
    shp = None


if shp is not None:

    class ShapelyBaseHandler(AbstractHandler):
        """
        Base handler for all Shapely geometry objects.
        Uses WKB (Well-Known Binary) format for serialization.
        """

        ext_type = 100  # Starting ext_type for Shapely objects

        @classmethod
        def packb(cls, geom: BaseGeometry) -> bytes:
            """Pack a shapely geometry into bytes using WKB format"""
            return dumps(geom)

        @classmethod
        def unpackb(cls, data: bytes):
            """Unpack bytes into a shapely geometry using WKB format"""
            return loads(data)

    class PointHandler(ShapelyBaseHandler):
        """Handler for Shapely Point objects"""

        ext_type = 101
        obj_type = Point

    class LineStringHandler(ShapelyBaseHandler):
        """Handler for Shapely LineString objects"""

        ext_type = 102
        obj_type = LineString

    class LinearRingHandler(ShapelyBaseHandler):
        """Handler for Shapely LinearRing objects"""

        ext_type = 103
        obj_type = LinearRing

    class PolygonHandler(ShapelyBaseHandler):
        """Handler for Shapely Polygon objects"""

        ext_type = 104
        obj_type = Polygon

    class MultiPointHandler(ShapelyBaseHandler):
        """Handler for Shapely MultiPoint objects"""

        ext_type = 105
        obj_type = MultiPoint

    class MultiLineStringHandler(ShapelyBaseHandler):
        """Handler for Shapely MultiLineString objects"""

        ext_type = 106
        obj_type = MultiLineString

    class MultiPolygonHandler(ShapelyBaseHandler):
        """Handler for Shapely MultiPolygon objects"""

        ext_type = 107
        obj_type = MultiPolygon

    class GeometryCollectionHandler(ShapelyBaseHandler):
        """Handler for Shapely GeometryCollection objects"""

        ext_type = 108
        obj_type = GeometryCollection
