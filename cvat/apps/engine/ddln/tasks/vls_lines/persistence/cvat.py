from cvat.apps.engine.ddln.geometry import Line, Point
from cvat.apps.engine.utils import grouper
from ..models import Runway
from ...utils import build_attrs_dict


class RunwayParseError(ValueError):
    pass


def iterate_runways(reader, reporter):
    if not reader._frame_annotation:
        return

    lons = {}
    lats = {}
    for shape in reader._frame_annotation.labeled_shapes:
        if shape.type != "rays":
            continue

        label = shape.label
        attrs = build_attrs_dict(shape)
        runway_id = attrs['Runway_ID']
        if label == 'Vertical line':
            if runway_id in lons:
                reporter.report_duplicated_rays(runway_id, is_lon=True)
            lons[runway_id] = (shape, attrs)
        elif label == 'Horizontal line':
            if runway_id in lats:
                reporter.report_duplicated_rays(runway_id, is_lon=False)
            lats[runway_id] = (shape, attrs)
        else:
            reporter.report_unknown_label(label)

    for runway_id in (lats.keys() - lons.keys()):
        reporter.report_missing_rays(runway_id, is_lon=True)

    for runway_id, lon in lons.items():
        lat = lats.get(runway_id)
        try:
            yield _parse_rays(lon, lat, reporter)
        except RunwayParseError as e:
            reporter._report(e.args[0])


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


def _parse_rays(lon, lat, reporter):
    lon_shape, lon_attrs = lon
    runway_id = lon_attrs['Runway_ID']
    left_visible = bool(int(lon_attrs['Left(1)']))
    right_visible = bool(int(lon_attrs['Right(2)']))
    center_visible = bool(int(lon_attrs['Central(3)']))
    left, right, center, lon_vanishing_point = _parse_lines(lon_shape)
    if lat:
        lat_shape, lat_attrs = lat
        start_visible = bool(int(lat_attrs['Beginning(1)']))
        designator_visible = bool(int(lat_attrs['Designator(2)']))
        end_visible = bool(int(lat_attrs['End(3)']))
        start, designator, end, lat_vanishing_point = _parse_lines(lat_shape)
    else:
        start_visible = end_visible = designator_visible = False
        start = designator = end = None
        lat_vanishing_point = None

    runway = Runway(runway_id, left, right, center, start, end, designator)
    runway.lon_vanishing_point = lon_vanishing_point
    runway.lat_vanishing_point = lat_vanishing_point
    runway.fix_order(reporter)
    runway.apply_visibility(left_visible, right_visible, center_visible, start_visible, end_visible, designator_visible)
    return runway


def _parse_lines(shape):
    points = [Point(x, y) for x, y in grouper(shape.points, 2)]
    vanishing_point = None if len(points) % 2 == 0 else points.pop()
    lines = [Line.by_two_points(a, b) for a, b in grouper(points, 2)]
    if len(lines) < 3:
        raise RunwayParseError("Not enough lines (should be at least 3)")
    first, second, third, *rest = lines
    return first, second, third, vanishing_point


def _get_points_list(runway):
    intersections = []
    for a in (runway.left_line, runway.center_line, runway.right_line):
        row = []
        for b in (runway.start_line, runway.designator_line, runway.end_line):
            row.append(a.intersect(b))
        intersections.append(row)

    lon_points = []
    for lon_index in range(3):
        lon_points.append(intersections[lon_index][0])
        lon_points.append(intersections[lon_index][2])
    if runway.lon_vanishing_point:
        lon_points.append(runway.lon_vanishing_point)
    lat_points = []
    for lat_index in range(3):
        lat_points.append(intersections[0][lat_index])
        lat_points.append(intersections[2][lat_index])
    if runway.lat_vanishing_point:
        lon_points.append(runway.lat_vanishing_point)

    lon_result = []
    for point in lon_points:
        lon_result.append(point.x)
        lon_result.append(point.y)
    lat_result = []
    for point in lat_points:
        lat_result.append(point.x)
        lat_result.append(point.y)
    return lon_result, lat_result


def _get_attributes(runway):
    lon_attrs = {
        "Runway_ID": runway.id,
        "Left(1)": int(runway.left_line is not None),
        "Right(2)": int(runway.right_line is not None),
        "Central(3)": int(runway.center_line is not None),
    }
    lat_attrs = {
        "Runway_ID": runway.id,
        "Beginning(1)": int(runway.start_line is not None),
        "Designator(2)": int(runway.designator_line is not None),
        "End(3)": int(runway.end_line is not None),
    }
    return lon_attrs, lat_attrs
