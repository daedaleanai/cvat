from cvat.apps.engine.utils import grouper
from ..models import RunwayPoint, Runway
from ...utils import build_attrs_dict


class RunwayParseError(ValueError):
    pass


def iterate_runways(reader, reporter):
    if not reader._frame_annotation:
        return

    try:
        runway = _parse_points(reader._frame_annotation.labeled_shapes)
        if runway:
            visibility_message = runway.validate_visibility()
            if visibility_message:
                reporter._report(visibility_message)
            yield runway
    except RunwayParseError as e:
        reporter._report(e.args[0])

    for shape in reader._frame_annotation.labeled_shapes:
        if shape.type != "polyline":
            continue
        try:
            runway = _parse_polyline(shape)
            visibility_message = runway.validate_visibility()
            if visibility_message:
                reporter._report(visibility_message)
            yield runway
        except RunwayParseError as e:
            reporter._report(e.args[0])


def write_runway(runway: Runway, writer):
    attributes = _get_attributes(runway)
    attributes = [writer._annotations.Attribute(name=name, value=value) for name, value in attributes.items()]

    shape = {
        "attributes": attributes,
        "points": _get_points_list(runway),
        "frame": writer._frame_id,
        "group": 0,
        "z_order": 0,
        "occluded": False,
        "type": "polyline",
        "label": "Runway",
    }
    writer._annotations.add_shape(writer._annotations.LabeledShape(**shape))


def _parse_polyline(shape):
    attrs = build_attrs_dict(shape)
    runway_id = attrs['Runway_ID']
    full_visible = _str_to_bool[attrs['Runway_visibility']]
    start_left_visible = attrs['Left_D(1)']
    start_right_visible = attrs['Right_D(2)']
    end_left_visible = attrs['Left_U(3)']
    end_right_visible = attrs['Right_U(4)']
    threshold_left_visible = attrs['Left_M(5)']
    threshold_right_visible = attrs['Right_M(6)']

    points = list(grouper(shape.points, 2))
    if len(points) != 6:
        raise RunwayParseError("Polyline has wrong amount of points. Expected 6, got {}".format(len(points)))
    start_left, start_right, end_left, end_right, threshold_left, threshold_right = points

    start_left = _build_point(start_left, start_left_visible)
    start_right = _build_point(start_right, start_right_visible)
    end_left = _build_point(end_left, end_left_visible)
    end_right = _build_point(end_right, end_right_visible)
    threshold_left = _build_point(threshold_left, threshold_left_visible)
    threshold_right = _build_point(threshold_right, threshold_right_visible)
    return Runway(
        runway_id, full_visible, start_left, start_right, end_left, end_right, threshold_left, threshold_right
    )


def _build_point(coordinates, visible):
    visible = bool(int(visible))
    x, y = [int(c) for c in coordinates]
    return RunwayPoint(visible, x, y)


def _parse_points(shapes):
    points = [s for s in shapes if s.type == "points"]
    if len(points) == 0:
        return None
    parsed = [_parse_point(p) for p in points]
    if len(parsed) != 6:
        raise RunwayParseError("Wrong amount of points. Expected 6 points, got {}".format(len(parsed)))
    point_by_label = {label: point for label, point in parsed}
    if len(point_by_label) != 6:
        seen = set()
        violators = set()
        for label, _ in parsed:
            if label in seen:
                violators.add(label)
            seen.add(label)
        raise RunwayParseError("Duplicated tag labels: {}".format(', '.join(violators)))

    start_left = point_by_label['First_tag']
    start_right = point_by_label['Second_tag']
    end_left = point_by_label['Third_tag']
    end_right = point_by_label['Fourth_tag']
    threshold_left = point_by_label['Fifth_tag']
    threshold_right = point_by_label['Sixth_tag']

    runway_id, full_visible = _parse_runway_info(shapes)
    return Runway(runway_id, full_visible, start_left, start_right, end_left, end_right, threshold_left,
                  threshold_right)


def _parse_point(shape):
    label = shape.label
    # for some reason, sometimes 'points' shape have the same point with the same coordinates multiple times
    # have to remove duplicates by using set
    points = {(int(x), int(y)) for x, y in grouper(shape.points, 2)}
    if len(points) > 1:
        raise RunwayParseError('Multiple points in element {!r}'.format(label))
    x, y = next(iter(points))
    visible = bool(int(build_attrs_dict(shape)['Tag_visibility']))
    point = RunwayPoint(visible, x, y)
    return label, point


def _parse_runway_info(shapes):
    first_tag = next((s for s in shapes if s.type == 'points' and s.label == 'First_tag'), None)
    if not first_tag:
        raise RunwayParseError("Missing first tag")
    attrs = build_attrs_dict(first_tag)
    visibility = _str_to_bool[attrs['Runway_visibility']]
    runway_id = attrs['Runway_ID']
    return runway_id, visibility


_str_to_bool = {"false": False, "true": True}


def _get_points_list(runway):
    # have to provide valid coordinates for all points to pass cvat validation,
    # but coordinates for non-visible threshold points are not stored in csv,
    # so have to interpolate them
    threshold_left = runway.threshold_left
    if not threshold_left.has_valid_coordinates():
        threshold_left = runway.start_left.get_midpoint(runway.end_left)

    threshold_right = runway.threshold_right
    if not threshold_right.has_valid_coordinates():
        threshold_right = runway.start_right.get_midpoint(runway.end_right)

    result = []
    points = [runway.start_left, runway.start_right, runway.end_left, runway.end_right, threshold_left, threshold_right]
    for point in points:
        result.append(point.x)
        result.append(point.y)
    return result


def _get_attributes(runway):
    return {
        "Runway_visibility": str(runway.full_visible).lower(),
        "Runway_ID": runway.id,
        "Left_D(1)": int(runway.start_left.visible),
        "Right_D(2)": int(runway.start_right.visible),
        "Left_U(3)": int(runway.end_left.visible),
        "Right_U(4)": int(runway.end_right.visible),
        "Left_M(5)": int(runway.threshold_left.visible),
        "Right_M(6)": int(runway.threshold_right.visible),
    }
