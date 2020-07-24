import math
import sys
from collections import defaultdict


def load_sequences(importer):
    frames_by_sequence_name = defaultdict(list)
    for raw_frame in importer.iterate_frames():
        frame = Frame(raw_frame.name, list(raw_frame.iterate_bboxes()))
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
