from cvat.apps.engine.ddln.geometry import Line, get_angle_between
from cvat.apps.engine.utils import grouper
from ..models import Runway
from ...utils import build_attrs_dict


class RunwayParseError(ValueError):
    pass


def write_runway(runway: Runway, writer):
    lon_attrs, lat_attrs = _get_attributes(runway)
    lon_attrs = [writer._annotations.Attribute(name=name, value=value) for name, value in lon_attrs.items()]
    lat_attrs = [writer._annotations.Attribute(name=name, value=value) for name, value in lat_attrs.items()]
    lon_points, lat_points = _get_points_list(runway)

    lon_shape = {
        "attributes": lon_attrs,
        "points": lon_points,
        "frame": writer._frame_id,
        "group": 0,
        "z_order": 0,
        "occluded": False,
        "type": "rays",
        "label": "Vertical line",
    }
    lat_shape = {
        "attributes": lat_attrs,
        "points": lat_points,
        "frame": writer._frame_id,
        "group": 0,
        "z_order": 0,
        "occluded": False,
        "type": "rays",
        "label": "Horizontal line",
    }
    writer._annotations.add_shape(writer._annotations.LabeledShape(**lon_shape))
    writer._annotations.add_shape(writer._annotations.LabeledShape(**lat_shape))


def _get_points_list(runway):
    # Coordinates for non-visible lines are not stored in csv,
    # so have to guess them
    lon_lines = _guess_lines(runway.lon_vanishing_point, runway.left_line, runway.center_line, runway.right_line)
    lat_lines = _guess_lines(runway.lat_vanishing_point, runway.start_line, runway.designator_line, runway.end_line)
    intersections = []
    for a in lon_lines:
        row = []
        for b in lat_lines:
            row.append(a.intersect(b))
        intersections.append(row)

    lon_points = []
    for lon_index in range(3):
        lon_points.append(intersections[lon_index][0])
        lon_points.append(intersections[lon_index][2])
    lat_points = []
    for lat_index in range(3):
        lat_points.append(intersections[0][lat_index])
        lat_points.append(intersections[2][lat_index])

    lon_result = []
    for point in lon_points:
        lon_result.append(point.x)
        lon_result.append(point.y)
    lat_result = []
    for point in lat_points:
        lat_result.append(point.x)
        lat_result.append(point.y)
    return lon_result, lat_result


def _guess_lines(vanishing_point, first, second, third):
    missing_lines_amount = sum(line is None for line in [first, second, third])
    if missing_lines_amount == 0:
        return first, second, third
    if missing_lines_amount == 1:
        if vanishing_point:
            if not first:
                dphi = get_angle_between(second.get_angle(), third.get_angle())
                first = Line.by_point_and_angle(vanishing_point, second.get_angle() - dphi)
            elif not second:
                dphi = get_angle_between(first.get_angle(), third.get_angle()) / 2
                second = Line.by_point_and_angle(vanishing_point, first.get_angle() + dphi)
            elif not third:
                dphi = get_angle_between(first.get_angle(), second.get_angle())
                third = Line.by_point_and_angle(vanishing_point, second.get_angle() + dphi)
        else:
            if not first:
                dx = third.c - second.c
                first = Line(second.a, second.b, second.c - dx)
            elif not second:
                dx = (third.c - first.c) / 2
                second = Line(third.a, third.b, third.c - dx)
            elif not third:
                dx = second.c - first.c
                third = Line(second.a, second.b, second.c + dx)
        return first, second, third
    if missing_lines_amount == 2:
        if vanishing_point:
            dphi = 0.175
            if first:
                second = Line.by_point_and_angle(vanishing_point, first.get_angle() + dphi)
                third = Line.by_point_and_angle(vanishing_point, second.get_angle() + dphi)
            elif second:
                first = Line.by_point_and_angle(vanishing_point, second.get_angle() - dphi)
                third = Line.by_point_and_angle(vanishing_point, second.get_angle() + dphi)
            elif third:
                second = Line.by_point_and_angle(vanishing_point, third.get_angle() - dphi)
                first = Line.by_point_and_angle(vanishing_point, second.get_angle() - dphi)
        else:
            dx = 10
            if first:
                second = Line(first.a, first.b, first.c + dx)
                third = Line(second.a, second.b, second.c + dx)
            elif second:
                first = Line(second.a, second.b, second.c - dx)
                third = Line(second.a, second.b, second.c + dx)
            elif third:
                second = Line(third.a, third.b, third.c - dx)
                first = Line(second.a, second.b, second.c - dx)
        return first, second, third
    raise RunwayParseError("All lines cannot be invisible")


def _get_attributes(runway):
    lon_attrs = {
        "Runway_ID": runway.id,
        "First_line(1)": int(runway.left_line is not None),
        "Second_line(2)": int(runway.right_line is not None),
        "Third_line(3)": int(runway.center_line is not None),
    }
    lat_attrs = {
        "Runway_ID": runway.id,
        "First_line(1)": int(runway.start_line is not None),
        "Second_line(2)": int(runway.designator_line is not None),
        "Third_line(3)": int(runway.end_line is not None),
    }
    return lon_attrs, lat_attrs
