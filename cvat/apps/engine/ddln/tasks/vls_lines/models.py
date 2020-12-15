import itertools
import math
from itertools import combinations
from typing import Optional

from cvat.apps.engine.ddln.geometry import Line, Point, get_angle_between, get_counterclockwise_angle

ANGLE_THRESHOLD = 0.05


class Runway:
    def __init__(
        self,
        id: str,
        left_line: Optional[Line],
        right_line: Optional[Line],
        center_line: Optional[Line],
        start_line: Optional[Line],
        end_line: Optional[Line],
        designator_line: Optional[Line],
    ):
        self.id = id
        self.left_line = left_line
        self.right_line = right_line
        self.center_line = center_line
        self.start_line = start_line
        self.end_line = end_line
        self.designator_line = designator_line
        self.lon_vanishing_point = None
        self.lat_vanishing_point = None

    @property
    def track_id(self):
        return self.id

    def calculate_vanishing_points(self, reporter):
        lon_lines = [self.left_line, self.center_line, self.right_line]
        self.lon_vanishing_point = self._calculate_vanishing_point(lon_lines, reporter, is_lon=True)
        lat_lines = [self.start_line, self.designator_line, self.end_line]
        self.lat_vanishing_point = self._calculate_vanishing_point(lat_lines, reporter, is_lon=False)

    def fix_order(self, reporter):
        if self.lon_vanishing_point:
            self._check_lon_order(reporter)
        else:
            self._check_parallel_lon_order(reporter)
        self._check_lat_order(reporter)

    def apply_visibility(
        self,
        left_visible,
        right_visible,
        center_visible,
        start_visible,
        end_visible,
        designator_visible
    ):
        if not left_visible:
            self.left_line = None
        if not right_visible:
            self.right_line = None
        if not center_visible:
            self.center_line = None
        if not start_visible:
            self.start_line = None
        if not end_visible:
            self.end_line = None
        if not designator_visible:
            self.designator_line = None

    def _check_lon_order(self, reporter):
        original = [self.left_line, self.center_line, self.right_line]
        max_angle = 0
        edges = None
        for a, b in itertools.combinations(original, 2):
            angle = get_angle_between(a.get_angle(), b.get_angle())
            if angle > max_angle:
                max_angle = angle
                edges = [a, b]
        new_center = next(filter(lambda line: line not in edges, original))
        new_left, new_right = edges
        if get_counterclockwise_angle(new_right.get_angle(), new_left.get_angle()) >= math.pi:
            new_left, new_right = new_right, new_left
        final = [new_left, new_center, new_right]
        if final != original:
            reporter.report_lon_disorder()

    def _check_parallel_lon_order(self, reporter):
        large_step = abs(self.left_line.c - self.right_line.c)
        small_step_a = abs(self.center_line.c - self.left_line.c)
        small_step_b = abs(self.center_line.c - self.right_line.c)
        if small_step_a >= large_step or small_step_b >= large_step:
            reporter.report_lon_disorder()

    def _check_lat_order(self, reporter):
        original = [self.end_line, self.designator_line, self.start_line]
        distant_point = self.lon_vanishing_point
        if not distant_point:
            # if longitudinal lines are parallel, just assume they are directed away from the camera
            distant_point = Line.by_point_and_angle(Point(0, 0), 0).intersect(self.center_line)
        if not distant_point:
            distant_point = Point(0, -10000)
        final = sorted(original, key=lambda line: distant_point.distance_to(line))
        if final != original:
            reporter.report_lat_disorder()

    def _calculate_vanishing_point(self, lines, reporter, is_lon):
        combs = ((a.intersect(b), get_lines_angle(a, b)) for a, b in combinations(lines, 2))
        points, angles = zip(*combs)
        points = [p for p in points if p]
        if not points:
            return None
        max_angle = max(angles)
        if max_angle <= ANGLE_THRESHOLD:
            return None

        average_point = get_average_point(points)
        # might be worth to double-check that lines are parallel
        # max_error = max(p.distance_to(average_point) for p in points)
        return average_point


def get_lines_angle(a, b):
    angle = get_angle_between(a.get_angle(), b.get_angle())
    return angle if angle < math.pi / 2 else (math.pi - angle)


def get_average_point(points):
    if not points:
        return None
    n = len(points)
    iterator = iter(points)
    average_point = next(iterator)
    for point in iterator:
        average_point += point
    average_point = Point(average_point.x / n, average_point.y / n)
    return average_point
