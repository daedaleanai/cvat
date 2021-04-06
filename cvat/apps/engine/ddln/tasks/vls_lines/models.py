import math
from itertools import combinations
from typing import Optional

from cvat.apps.engine.ddln.geometry import Line, Point, get_angle_between

ANGLE_THRESHOLD = 5 * math.pi / 180
ERROR_THRESHOLD = 30


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
        lon_lines = [line for line in lon_lines if line is not None]
        if len(lon_lines) > 1:
            self.lon_vanishing_point = self._calculate_vanishing_point(lon_lines, reporter, is_lon=True)
        lat_lines = [self.start_line, self.designator_line, self.end_line]
        if all(line is not None for line in lat_lines):
            self.lat_vanishing_point = self._calculate_vanishing_point(lat_lines, reporter, is_lon=False)

    def fix_order(self, reporter):
        self._check_lon_order(reporter)
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

    def get_invisible_lines(self):
        result = []
        if self.left_line is None:
            result.append("left edge")
        if self.right_line is None:
            result.append("right edge")
        if self.center_line is None:
            result.append("central line")
        if self.start_line is None:
            result.append("beginning")
        if self.designator_line is None:
            result.append("designator")
        if self.end_line is None:
            result.append("end")
        return tuple(result)


    def _check_lon_order(self, reporter):
        # end line is intentionally omitted to avoid false-positives
        lat_lines = [self.start_line, self.designator_line]
        if any(line is None for line in lat_lines):
            return
        left_points = [line.intersect(self.left_line) for line in lat_lines]
        right_points = [line.intersect(self.right_line) for line in lat_lines]
        if any(p is None for p in left_points) or any(p is None for p in right_points):
            reporter.report_lon_disorder()
            return
        left_points_side, is_left_correct = _get_points_side(left_points, self.center_line)
        right_points_side, is_right_correct = _get_points_side(right_points, self.center_line)
        if not (is_left_correct and is_right_correct and left_points_side == -right_points_side):
            reporter.report_lon_disorder()

    def _check_lat_order(self, reporter):
        original = [self.end_line, self.designator_line, self.start_line]
        if any(line is None for line in original):
            return
        reference_line = self.center_line or self.left_line or self.right_line
        distant_point = self.lon_vanishing_point
        if not (distant_point and reference_line):
            return
        final = sorted(original, key=lambda line: distant_point.distance_to(reference_line.intersect(line)))
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
        max_error = max(p.distance_to(average_point) for p in points)
        if max_error > ERROR_THRESHOLD:
            reporter.report_not_crossing(max_error)
        return average_point


def _get_points_side(points, line):
    # iterate points and figure out on which side of the line the points are placed
    # returns:
    #     -1, True - if all the points are to the left of the line
    #     1, True - if all the points are to the right of the line
    #     0, True - if all the points lie on the line
    #     *, False - if some of the points are on the other side of the line
    if len(points) == 0:
        return 0, False
    distances = (p.signed_distance_to(line) for p in points)
    sides = (-1 if d < 0 else (1 if d > 0 else 0) for d in distances)
    result = next(sides)
    is_correct = all(v == result or v == 0 for v in sides)
    return result, is_correct


def get_lines_angle(a, b):
    angle = get_angle_between(a.get_angle(), b.get_angle())
    return angle if angle < math.pi / 2 else (math.pi - angle)


def get_average_point(points):
    if not points:
        return None
    n = len(points)
    sum = Point(0, 0)
    for p in points:
        sum += p
    average_point = Point(sum.x / n, sum.y / n)
    return average_point
