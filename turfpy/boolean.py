"""
This module implements some of the spatial analysis techniques and processes used to
understand the patterns and relationships of geographic features.
This is mainly inspired by turf.js.
link: http://turfjs.org/
"""

import json
from typing import Optional, Tuple

from geojson import Feature, LineString, MultiPolygon, Point, Polygon
from shapely import to_geojson
from shapely.geometry import LineString as ShapelyLineString
from shapely.geometry import MultiPoint as ShapelyMultiPoint
from shapely.geometry import Point as ShapelyPoint
from shapely.geometry import Polygon as ShapelyPolygon
from shapely.geometry import shape

from turfpy.feature_conversion import polygon_to_line
from turfpy.measurement import boolean_point_in_polygon
from turfpy.meta import flatten_each
from turfpy.misc import line_intersect


def __is_point_on_line(line_string: LineString, point: Point) -> bool:
    """
    Determine if point is on a line

    :param line_string: GeoJSON LineString
    :type line_string: LineString
    :param point: GeoJSON Point
    :type point: Point
    :returns: True if the point is on the line
    :rtype: bool
    """
    coordinates = line_string["coordinates"]
    pt_coordinates = point["coordinates"]

    for i in range(len(coordinates) - 1):
        if __is_point_on_line_segment(
            coordinates[i], coordinates[i + 1], pt_coordinates, False, None, None
        ):
            return True
    return False


def __is_line_on_line(line_string_1: LineString, line_string_2: LineString) -> bool:
    """
    Determine if line is on line

    :param line_string_1: GeoJSON LineString
    :type line_string_1: LineString
    :param line_string_2: GeoJSON LineString
    :type line_string_2: LineString
    :returns: True if the line is on the other line
    :rtype: bool
    """
    do_lines_intersect = line_intersect(line_string_1, line_string_2)

    if len(do_lines_intersect["features"]) > 0:
        return True
    return False


def __is_line_in_poly(polygon: Polygon, line_string: LineString) -> bool:
    """
    Determine if line is in a polygon


    :param polygon: GeoJSON Polygon
    :type polygon: Polygon
    :param line_string: GeoJSON LineString
    :type line_string: LineString
    :returns: True if the line is in the polygon
    :rtype: bool
    """
    for coord in line_string["coordinates"]:
        if boolean_point_in_polygon(Point(coordinates=coord), polygon):
            return True

    do_lines_intersect = line_intersect(line_string, polygon_to_line(polygon))

    if len(do_lines_intersect["features"]) > 0:
        return True

    return False


def __is_poly_in_poly(feature1: Polygon, feature2: Polygon) -> bool:
    """
    Determine if a polygon is in another polygon

    :param feature1: GeoJSON Polygon
    :type feature1: Polygon
    :param feature2: GeoJSON Polygon
    :type feature2: Polygon
    :returns: True if the polygon is in the other polygon
    :rtype: bool
    """
    for coord1 in feature1["coordinates"][0]:
        if boolean_point_in_polygon(Point(coordinates=coord1), feature2):
            return True

    for coord2 in feature2["coordinates"][0]:
        if boolean_point_in_polygon(Point(coordinates=coord2), feature1):
            return True

    do_lines_intersect = line_intersect(
        polygon_to_line(feature1), polygon_to_line(feature2)
    )

    if len(do_lines_intersect["features"]) > 0:
        return True

    return False


def __compare_coords(pair1: list, pair2: list) -> bool:
    """
    Compare coordinates to see if they match

    :param pair1: pair of coordinates
    :type pair1: list
    :param pair2: pair of coordinates
    :type pair2: list
    :returns: True if the two pairs of coordinates match
    :rtype: bool
    """

    return pair1[0] == pair2[0] and pair1[1] == pair2[1]


def __disjoint(feature_1: Feature, feature_2: Feature) -> bool:
    """
    Disjoint operation for simple Geometries (Point/LineString/Polygon)

    :param feature_1: GeoJSON Feature or Geometry
    :type feature_1: Feature
    :param feature_2: GeoJSON Feature or Geometry
    :type feature_2: Feature
    :param ignore_self_intersections: whether to ignore self intersections
    :type ignore_self_intersections: bool
    :returns: True if the two geometries do not touch or overlap.
    :rtype: bool
    """

    geom1_type = feature_1["geometry"]["type"]
    geom2_type = feature_2["geometry"]["type"]

    if geom1_type == "Point":
        if geom2_type == "Point":
            return not __compare_coords(
                feature_1["geometry"]["coordinates"],
                feature_2["geometry"]["coordinates"],
            )
        elif geom2_type == "LineString":
            return not __is_point_on_line(feature_2["geometry"], feature_1["geometry"])
        elif geom2_type == "Polygon":
            return not boolean_point_in_polygon(
                feature_1["geometry"], feature_2["geometry"]
            )

    elif geom1_type == "LineString":
        if geom2_type == "Point":
            return not __is_point_on_line(feature_1["geometry"], feature_2["geometry"])
        elif geom2_type == "LineString":
            return not __is_line_on_line(feature_1["geometry"], feature_2["geometry"])
        elif geom2_type == "Polygon":
            return not __is_line_in_poly(feature_2["geometry"], feature_1["geometry"])

    elif geom1_type == "Polygon":
        if geom2_type == "Point":
            return not boolean_point_in_polygon(
                feature_2["geometry"], feature_1["geometry"]
            )
        elif geom2_type == "LineString":
            return not __is_line_in_poly(feature_1["geometry"], feature_2["geometry"])
        elif geom2_type == "Polygon":
            return not __is_poly_in_poly(feature_2["geometry"], feature_1["geometry"])

    return False


def boolean_disjoint(feature_1: Feature, feature_2: Feature) -> bool:
    """
    Boolean-disjoint returns (TRUE) if the two geometries do not touch or overlap.

    :param feature_1: GeoJSON Feature or Geometry
    :type feature_1: Feature
    :param feature_2: GeoJSON Feature or Geometry
    :type feature_2: Feature
    :returns: True if the two geometries do not touch or overlap.
    :rtype: bool


    Example:

    >>> from turfpy.boolean import boolean_disjoint
    >>> from geojson import Feature, Polygon
    >>> boolean_disjoint()

    """

    bool_result = True

    def check_disjoint(flatten1, index1, feature_collection1):
        nonlocal bool_result
        if not bool_result:
            return False

        def inner_check(flatten2, index2, feature_collection2):
            nonlocal bool_result
            if not bool_result:
                return False
            bool_result = __disjoint(flatten1, flatten2)

        flatten_each(feature_2, inner_check)

    flatten_each(feature_1, check_disjoint)

    return bool_result


def boolean_intersects(feature_1: Feature, feature_2: Feature) -> bool:
    """
    Boolean-intersects returns (TRUE) if the intersection of
    the two geometries is NOT an empty set.

    :param feature_1: GeoJSON Feature or Geometry
    :type feature_1: Feature
    :param feature_2: GeoJSON Feature or Geometry
    :type feature_2: Feature
    :returns: True if the intersection of the two geometries is NOT an empty set.
    :rtype: bool
    """

    bool_result = False

    def check_intersection(flatten1, index1, feature_collection1):
        nonlocal bool_result
        if bool_result:
            return True

        def inner_check(flatten2, index2, feature_collection2):
            nonlocal bool_result
            if bool_result:
                return True
            bool_result = not boolean_disjoint(
                flatten1["geometry"], flatten2["geometry"]
            )

        flatten_each(feature_2, inner_check)

    flatten_each(feature_1, check_intersection)

    return bool_result


def __is_point_in_multipoint(
    point: ShapelyPoint, multipoint: ShapelyMultiPoint
) -> bool:
    return any(point.equals(ShapelyPoint(coord)) for coord in multipoint.geoms)


def __is_multipoint_in_multipoint(
    multipoint1: ShapelyMultiPoint, multipoint2: ShapelyMultiPoint
) -> bool:
    return all(
        any(
            ShapelyPoint(coord1).equals(ShapelyPoint(coord2))
            for coord2 in multipoint2.geoms
        )
        for coord1 in multipoint1.geoms
    )


def __is_multipoint_on_line(
    multipoint: ShapelyMultiPoint, line: ShapelyLineString
) -> bool:
    found_inside_point = False

    for point in multipoint.geoms:
        if not boolean_point_on_line(point, line):
            return False
        if not found_inside_point:
            found_inside_point = boolean_point_on_line(
                point, line, ignore_end_vertices=True
            )

    return found_inside_point


def __is_multipoint_in_poly(
    multipoint: ShapelyMultiPoint, poly: ShapelyPolygon
) -> bool:
    # for coord in multipoint.geoms:
    #     print(ShapelyPoint(coord).within(poly))
    # return all(ShapelyPoint(coord).within(poly) for coord in multipoint.geoms)
    output = True
    one_inside = False
    is_inside = False

    for coord in multipoint.geoms:
        polygon_type = poly.geom_type
        if polygon_type == "Polygon":
            geojson_poly = Polygon(
                coordinates=json.loads(to_geojson(poly))["coordinates"]
            )
        elif polygon_type == "MultiPolygon":
            geojson_poly = MultiPolygon(
                coordinates=json.loads(to_geojson(poly))["coordinates"]
            )
        print("is_inside", is_inside)
        is_inside = boolean_point_in_polygon(
            json.loads(to_geojson(coord)), geojson_poly
        )

        if not is_inside:
            output = False
            break
        if not one_inside:
            is_inside = boolean_point_in_polygon(
                json.loads(to_geojson(coord)),
                geojson_poly,
                ignore_boundary=True,
            )
    print("is_inside", is_inside)
    return output and is_inside


def boolean_point_on_line(
    pt: Point,
    line: LineString,
    ignore_end_vertices: bool = False,
    epsilon: Optional[float] = None,
) -> bool:
    pt_coords = pt.coords[0]
    line_coords = list(line.coords)

    for i in range(len(line_coords) - 1):
        ignore_boundary = False
        ignore_boundary_type = None
        if ignore_end_vertices:
            if i == 0:
                ignore_boundary = True
                ignore_boundary_type = "start"
            if i == len(line_coords) - 2:
                ignore_boundary = True
                ignore_boundary_type = "end"
            if i == 0 and i + 1 == len(line_coords) - 1:
                ignore_boundary = True
                ignore_boundary_type = "both"

        if __is_point_on_line_segment(
            line_coords[i],
            line_coords[i + 1],
            pt_coords,
            ignore_boundary,
            ignore_boundary_type,
            epsilon,
        ):
            return True

    return False


def __is_point_on_line_segment(
    line_segment_start: Tuple[float, float],
    line_segment_end: Tuple[float, float],
    pt: Tuple[float, float],
    exclude_boundary: Optional[bool],
    exclude_boundary_type: Optional[str],
    epsilon: Optional[float],
) -> bool:
    x, y = pt
    x1, y1 = line_segment_start
    x2, y2 = line_segment_end
    dxc = x - x1
    dyc = y - y1
    dxl = x2 - x1
    dyl = y2 - y1
    cross = dxc * dyl - dyc * dxl

    if epsilon is not None:
        if abs(cross) > epsilon:
            return False
    elif cross != 0:
        return False

    if not exclude_boundary:
        if abs(dxl) >= abs(dyl):
            return dxl > 0 if x1 <= x <= x2 else x2 <= x <= x1
        return dyl > 0 if y1 <= y <= y2 else y2 <= y <= y1
    elif exclude_boundary and exclude_boundary_type == "start":
        if abs(dxl) >= abs(dyl):
            return dxl > 0 if x1 < x <= x2 else x2 <= x < x1
        return dyl > 0 if y1 < y <= y2 else y2 <= y < y1
    elif exclude_boundary and exclude_boundary_type == "end":
        if abs(dxl) >= abs(dyl):
            return dxl > 0 if x1 <= x < x2 else x2 < x <= x1
        return dyl > 0 if y1 <= y < y2 else y2 < y <= y1
    elif exclude_boundary and exclude_boundary_type == "both":
        if abs(dxl) >= abs(dyl):
            return dxl > 0 if x1 < x < x2 else x2 < x < x1
        return dyl > 0 if y1 < y < y2 else y2 < y < y1

    return False


def boolean_within(feature_1: Feature, feature_2: Feature) -> bool:
    """
    Boolean-within returns (TRUE) if the first geometry is
    completely within the second geometry. The interiors
    of both geometries must intersect and, the interior
    and boundary of the primary (geometry a) must not
    intersect the exterior of the secondary (geometry b).

    :param feature_1: GeoJSON Feature or Geometry
    :type feature_1: Feature
    :param feature_2: GeoJSON Feature or Geometry
    :type feature_2: Feature
    :returns: True if the first geometry is
    completely within the second geometry.
    :rtype: bool
    """
    geom1 = shape(feature_1["geometry"])
    geom2 = shape(feature_2["geometry"])
    type1 = geom1.geom_type
    type2 = geom2.geom_type

    if type1 == "Point":
        if type2 == "MultiPoint":
            return __is_point_in_multipoint(geom1, geom2)
        elif type2 == "LineString":
            return geom1.within(geom2)
        elif type2 in ["Polygon", "MultiPolygon"]:
            return geom1.within(geom2)
        else:
            raise ValueError(f"feature2 {type2} geometry not supported")
    elif type1 == "MultiPoint":
        if type2 == "MultiPoint":
            return __is_multipoint_in_multipoint(geom1, geom2)
        elif type2 == "LineString":
            return __is_multipoint_on_line(geom1, geom2)
        elif type2 in ["Polygon", "MultiPolygon"]:
            return __is_multipoint_in_poly(geom1, geom2)
        else:
            raise ValueError(f"feature2 {type2} geometry not supported")
    elif type1 == "LineString":
        if type2 == "LineString":
            return geom1.within(geom2)
        elif type2 in ["Polygon", "MultiPolygon"]:
            return geom1.within(geom2)
        else:
            raise ValueError(f"feature2 {type2} geometry not supported")
    elif type1 == "Polygon":
        if type2 in ["Polygon", "MultiPolygon"]:
            return geom1.within(geom2)
        else:
            raise ValueError(f"feature2 {type2} geometry not supported")
    else:
        raise ValueError(f"feature1 {type1} geometry not supported")
