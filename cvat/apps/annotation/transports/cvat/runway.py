from cvat.apps.annotation.structures import RunwayPoint, Runway
from cvat.apps.annotation.transports.cvat.utils import grouper, build_attrs_dict


class RunwayParseError(ValueError):
    pass


def parse_polyline(shape):
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


def parse_points(shapes):
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


