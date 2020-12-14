import math

from cvat.apps.engine.ddln.geometry import Line, Point, PolarPoint
from ..models import Runway


def iterate_runways(reader, reporter):
    for row in reader._reader:
        runway_id, *lines_data = row
        assert len(lines_data) == 12  # 6 lines, each line is represented by 2 values
        left = from_row(lines_data[0:2], reader.image_width, reader.image_height)
        right = from_row(lines_data[2:4], reader.image_width, reader.image_height)
        center = from_row(lines_data[4:6], reader.image_width, reader.image_height)
        start = from_row(lines_data[6:8], reader.image_width, reader.image_height)
        end = from_row(lines_data[8:10], reader.image_width, reader.image_height)
        designator = from_row(lines_data[10:12], reader.image_width, reader.image_height)
        runway = Runway(runway_id, left, right, center, start, end, designator)
        runway.calculate_vanishing_points(reporter)
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
    distance = format(distance, ".3f")
    return angle, distance
