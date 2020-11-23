from typing import Optional


class RunwayPoint:
    def __init__(self, visible: bool, x: Optional[int], y: Optional[int]):
        # for non-visible threshold points coordinates are not specified, i.e. their values are set to None
        self.visible = visible
        self.x = x
        self.y = y

    def has_valid_coordinates(self):
        return self.x is not None and self.y is not None

    def get_midpoint(self, other: 'RunwayPoint', visible=False):
        x = self.x + (other.x - self.x) // 2
        y = self.y + (other.y - self.y) // 2
        return RunwayPoint(visible, x, y)


class Runway:
    def __init__(
        self,
        id: str,
        full_visible: bool,
        start_left: RunwayPoint,
        start_right: RunwayPoint,
        end_left: RunwayPoint,
        end_right: RunwayPoint,
        threshold_left: RunwayPoint,
        threshold_right: RunwayPoint
    ):
        # non-visible threshold points coordinates are not exported, so unset them
        if not threshold_left.visible:
            threshold_left = RunwayPoint(False, None, None)
        if not threshold_right.visible:
            threshold_right = RunwayPoint(False, None, None)

        self.id = id
        self.full_visible = full_visible
        self.start_left = start_left
        self.start_right = start_right
        self.end_left = end_left
        self.end_right = end_right
        self.threshold_left = threshold_left
        self.threshold_right = threshold_right

    @property
    def track_id(self):
        return self.id

    @property
    def points(self):
        yield 'start_left', self.start_left
        yield 'start_right', self.start_right
        yield 'end_left', self.end_left
        yield 'end_right', self.end_right

    def validate_visibility(self, reporter):
        if all(p.visible for _, p in self.points) and not self.full_visible:
            reporter.report_likely_full_visible()
        if self.full_visible:
            violators = [n for n, p in self.points if not p.visible]
            reporter.report_inconsistent_visibility(violators)
