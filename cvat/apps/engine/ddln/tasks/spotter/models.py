import math
import sys


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


# TODO(gy): store these in labels
label_by_class_id = {
    "1": "Drone",
    "3": "Flying bird",
    "4": "Fixed wing aircraft",
    "5": "Helicopter",
    "6": "Hot air balloon",
    "7": "Parachute",
    "99": "Exclusion",
    "100": "Unknown",
}
