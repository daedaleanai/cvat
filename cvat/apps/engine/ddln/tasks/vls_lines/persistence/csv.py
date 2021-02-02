import math

from cvat.apps.engine.ddln.geometry import Line, Point, PolarPoint, get_angle_between
from ..models import Runway


def iterate_runways(reader, reporter):
    for row in reader._reader:
        runway_id, *lines_data = row
        if len(lines_data) != 12:  # 6 lines, each line is represented by 2 values
            reporter.report_wrong_values_amount(12, len(lines_data))
            continue
        left = from_row(lines_data[0:2], reader.image_width, reader.image_height)
        right = from_row(lines_data[2:4], reader.image_width, reader.image_height)
        center = from_row(lines_data[4:6], reader.image_width, reader.image_height)
        start = from_row(lines_data[6:8], reader.image_width, reader.image_height)
        end = from_row(lines_data[8:10], reader.image_width, reader.image_height)
        designator = from_row(lines_data[10:12], reader.image_width, reader.image_height)
        runway = Runway(runway_id, left, right, center, start, end, designator)
        runway.calculate_vanishing_points(reporter)
        try:
            fake_invisible_lines(runway)
        except ValueError as e:
            reporter._report(e.args[0])
            continue
        yield runway


def write_runway(runway: Runway, writer):
    writer._writer.writerow((
        runway.id,
        *as_row(runway.left_line, writer.image_width, writer.image_height),
        *as_row(runway.right_line, writer.image_width, writer.image_height),
        *as_row(runway.center_line, writer.image_width, writer.image_height),
        *as_row(runway.start_line, writer.image_width, writer.image_height),
        *as_row(runway.end_line, writer.image_width, writer.image_height),
        *as_row(runway.designator_line, writer.image_width, writer.image_height),
    ))


def from_row(row, width, height):
    angle, distance = row
    if angle == '' and distance == '':
        return None
    unit = height / 2
    center = Point(width / 2, height / 2)
    angle = -float(angle)
    distance = float(distance)
    distance = unit * distance
    angle = angle * math.pi / 180
    polar_point = PolarPoint(distance, angle + math.pi / 2)
    touch_point = polar_point.to_cartesian_coordinates(center)
    return Line.by_point_and_angle(touch_point, angle)


def as_row(line, width, height):
    if not line:
        return '', ''
    unit = height / 2
    center = Point(width / 2, height / 2)
    horizontal_line = Line.by_point_and_angle(center, 0)
    distance = center.distance_to(line)
    # need minus here, because CVAT y axis is opposite to output y axis
    angle = -line.get_angle()
    intersection = line.intersect(horizontal_line)
    if intersection:
        if intersection.x < width / 2:
            angle += math.pi
    else:
        vertical_line = Line.by_point_and_angle(center, math.pi / 2)
        vertical_intersection = line.intersect(vertical_line)
        if vertical_intersection.y < height / 2:
            angle += math.pi

    distance = distance / unit
    angle = angle % (2 * math.pi)
    angle = angle * 180 / math.pi
    angle = format(angle, ".2f")
    distance = format(distance, ".6f")
    return angle, distance


def fake_invisible_lines(runway):
    # Coordinates for non-visible lines are not stored in csv,
    # so have to guess them
    lon_lines = guess_lines(runway.lon_vanishing_point, runway.left_line, runway.center_line, runway.right_line)
    runway.left_line, runway.center_line, runway.right_line = lon_lines
    lat_lines = guess_lines(runway.lat_vanishing_point, runway.start_line, runway.designator_line, runway.end_line)
    runway.start_line, runway.designator_line, runway.end_line = lat_lines


def guess_lines(vanishing_point, first, second, third):
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
    raise ValueError("All lines cannot be invisible")
