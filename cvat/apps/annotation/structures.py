import math
import sys
from collections import defaultdict
from typing import Optional


def load_sequences(importer):
    frames_by_sequence_name = defaultdict(list)
    for raw_frame in importer.iterate_frames():
        frame = Frame(raw_frame.name, list(raw_frame.iterate_bboxes()))
        if hasattr(raw_frame, 'index'):
            frame.index = raw_frame.index
        frames_by_sequence_name[raw_frame.sequence_name].append(frame)

    sequences = []
    for sequence_name, frames in frames_by_sequence_name.items():
        frames.sort(key=lambda f: f.name)
        sequences.append(Sequence(sequence_name, frames))

    return sequences


class Sequence:
    def __init__(self, name, frames=None):
        if frames is None:
            frames = []
        self.name = name
        self.frames = frames


class Frame:
    def __init__(self, name, bboxes):
        self.name = name
        self.index = None
        self.bboxes = bboxes
        self.bbox_by_track_id = {b.track_id: b for b in bboxes}

    def __repr__(self):
        return 'Frame<{}>'.format(self.name)


class BoundingBox:
    def __init__(self, left, top, width, height):
        self.left = left
        self.top = top
        self.width = width
        self.height = height

    @classmethod
    def from_two_corners(cls, xtl, ytl, xbr, ybr):
        assert xbr >= xtl and ybr >= ytl
        return cls(xtl, ytl, xbr-xtl, ybr-ytl)

    @property
    def right(self):
        return self.left + self.width

    @property
    def bottom(self):
        return self.top + self.height

    @property
    def area(self):
        return self.width * self.height

    def compute_iou(self, other):
        """ Computes intersection over union between self and other. """
        area1 = self.area
        area2 = other.area

        if area1 <= sys.float_info.epsilon or area2 <= sys.float_info.epsilon:
            return 1.0

        intersection = self.intersect(other)
        if not intersection:
            return 0.0

        inter_area = intersection.area
        return inter_area / (area1 + area2 - inter_area)

    def intersect(self, other):
        """ Computes intersection over two boxes self and other. """
        left = max(self.left, other.left)
        right = min(self.right, other.right)
        if right <= left:
            return None
        top = max(self.top, other.top)
        bottom = min(self.bottom, other.bottom)
        if bottom <= top:
            return None
        return BoundingBox(left, top, right - left, bottom - top)

    def get_embracing_box(self, other):
        left = min(self.left, other.left)
        right = max(self.right, other.right)
        top = min(self.top, other.top)
        bottom = max(self.bottom, other.bottom)
        return BoundingBox(left, top, right - left, bottom - top)

    def almost_equals(self, other, **kwargs):
        return (
            isinstance(other, BoundingBox)
            and math.isclose(self.left, other.left, **kwargs)
            and math.isclose(self.top, other.top, **kwargs)
            and math.isclose(self.width, other.width, **kwargs)
            and math.isclose(self.height, other.height, **kwargs)
        )

    def __repr__(self):
        return "BoundingBox({}, {}, {}, {})".format(self.left, self.top, self.width, self.height)


class LabeledBoundingBox(BoundingBox):
    def __init__(self, left, top, width, height, class_id, track_id):
        super().__init__(left, top, width, height)
        self.class_id = class_id
        self.track_id = track_id
        self.score = None
        self.source = None

    @classmethod
    def from_two_corners(cls, xtl, ytl, xbr, ybr, class_id, track_id):
        assert xbr >= xtl and ybr >= ytl
        return cls(xtl, ytl, xbr - xtl, ybr - ytl, class_id, track_id)


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

    @classmethod
    def from_row(cls, row):
        visible, x, y = row
        visible = bool(int(visible))
        x = _deserialize(x)
        y = _deserialize(y)
        return cls(visible, x, y)

    def as_row(self):
        return int(self.visible), _serialize(self.x), _serialize(self.y)


def _serialize(coordinate):
    return '' if coordinate is None else coordinate


def _deserialize(input):
    return None if input == '' else int(input)


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
        return "Runway is visible, but its {} points is not".format(', '.join(violators))

    def get_points_list(self):
        threshold_left = self.threshold_left
        if not threshold_left.has_valid_coordinates():
            threshold_left = self.start_left.get_midpoint(self.end_left)

        threshold_right = self.threshold_right
        if not threshold_right.has_valid_coordinates():
            threshold_right = self.start_right.get_midpoint(self.end_right)

        result = []
        points = [self.start_left, self.start_right, self.end_left, self.end_right, threshold_left, threshold_right]
        for point in points:
            result.append(point.x)
            result.append(point.y)
        return result

    def get_attributes(self):
        return {
            "Runway_visibility": str(self.full_visible).lower(),
            "Runway_ID": self.id,
            "Left_D(1)": int(self.start_left.visible),
            "Right_D(2)": int(self.start_right.visible),
            "Left_U(3)": int(self.end_left.visible),
            "Right_U(4)": int(self.end_right.visible),
            "Left_M(5)": int(self.threshold_left.visible),
            "Right_M(6)": int(self.threshold_right.visible),
        }


label_by_class_id = {
    "1": "Drone",
    "3": "Flying bird",
    "4": "Fixed wing aircraft",
    "5": "Helicopter",
    "100": "Unknown",
}
