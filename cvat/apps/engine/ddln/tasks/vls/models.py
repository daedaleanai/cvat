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

    def validate_visibility(self):
        """Returns None if runway visibility is valid, error message otherwise"""
        if not self.full_visible:
            return None
        violators = set()
        for point_name in ('start_left', 'start_right', 'end_left', 'end_right'):
            point = getattr(self, point_name)
            if not point.visible:
                name = point_name.replace('_', ' ')
                violators.add(name)
        if not violators:
            return None
        return "Runway is visible, but its {} points are not".format(', '.join(violators))
