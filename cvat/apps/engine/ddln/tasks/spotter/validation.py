from .models import label_by_class_id
from ..validation import BaseValidationReporter


def validate(sequences, reporter=None, jump_threshold=10):
    if reporter is None:
        reporter = SpotterValidationReporter()
    for seq in sequences:
        reporter.sequence = seq.name
        class_id_by_track_id = {}
        previous_frame = None
        sequence_track_ids = set()

        for frame in seq.frames:
            reporter.frame = frame.name
            reporter.frame_index = frame.index
            reporter.count_frame(seq.name)

            frame_track_ids = set()
            duplicated_track_ids = set()
            for bbox_index, bbox in enumerate(frame.objects, start=1):
                reporter.bbox_index = bbox_index

                if bbox.track_id in frame_track_ids:
                    duplicated_track_ids.add(bbox.track_id)
                frame_track_ids.add(bbox.track_id)
                sequence_track_ids.add(bbox.track_id)

                _validate_coordinates(bbox, reporter)
                _validate_attributes(bbox, reporter)
                _validate_class_immutability(bbox, class_id_by_track_id, reporter)
                _validate_position_change(bbox, previous_frame, jump_threshold, reporter)

            reporter.bbox_index = None
            for track_id in duplicated_track_ids:
                reporter.report_track_id_duplication(track_id)
            previous_frame = frame

        reporter.frame = None
        reporter.frame_index = None
        _validate_track_id_are_consecutive(sequence_track_ids, reporter)
    return reporter


def _validate_attributes(bbox, reporter):
    try:
        int(bbox.track_id)
    except (TypeError, ValueError):
        reporter.report_invalid_track_id_value(bbox.track_id)

    if bbox.class_id not in label_by_class_id:
        reporter.report_invalid_class_id_value(bbox.class_id)


def _validate_class_immutability(bbox, class_id_by_track_id, reporter):
    prev_class_id = class_id_by_track_id.get(bbox.track_id, bbox.class_id)
    if prev_class_id != bbox.class_id:
        reporter.report_class_id_change(prev_class_id, bbox.class_id)
    class_id_by_track_id[bbox.track_id] = bbox.class_id


def _validate_track_id_are_consecutive(sequence_track_ids, reporter):
    expected = range(1, len(sequence_track_ids) + 1)
    expected = set(map(str, expected))
    if sequence_track_ids != expected:
        reporter.report_track_id_non_consecutive(sequence_track_ids)


def _validate_position_change(bbox, previous_frame, jump_threshold, reporter):
    previous_bbox = previous_frame and previous_frame.object_by_track_id.get(bbox.track_id)
    if not (previous_bbox and is_valid_bbox(previous_bbox) and is_valid_bbox(bbox)):
        return

    if bbox.almost_equals(previous_bbox, abs_tol=1e-5):
        reporter.report_no_move()
        return

    embracing_bbox = bbox.get_embracing_box(previous_bbox)
    width_jump = embracing_bbox.width / (bbox.width + previous_bbox.width)
    height_jump = embracing_bbox.height / (bbox.height + previous_bbox.height)
    if max(width_jump, height_jump) > jump_threshold:
        reporter.report_large_jump()


def _validate_coordinates(bbox, reporter):
    for coordinate in ('left', 'top', 'right', 'bottom'):
        value = getattr(bbox, coordinate)
        if not (0 <= value <= 1):
            reporter.report_out_of_bounds(coordinate, value)

    if bbox.left > bbox.right:
        reporter.report_left_gt_right()
    if bbox.top > bbox.bottom:
        reporter.report_top_gt_bottom()


def is_valid_bbox(bbox):
    return (
        all(0 <= getattr(bbox, c) <= 1 for c in ('left', 'top', 'right', 'bottom'))
        and bbox.left <= bbox.right
        and bbox.top <= bbox.bottom
    )


class SpotterValidationReporter(BaseValidationReporter):
    object_name = 'Box'

    def report_out_of_bounds(self, coordinate, value):
        self._report("{} value {} is not within [0, 1] interval".format(coordinate, value))

    def report_left_gt_right(self):
        self._report("left coordinate is greater than right value")

    def report_top_gt_bottom(self):
        self._report("top coordinate is greater than bottom coordinate")

    def report_track_id_duplication(self, track_id):
        self._report("track-id '{}' is duplicated on the frame".format(track_id))

    def report_invalid_track_id_value(self, value):
        self._report("track-id has invalid value: '{}'".format(value))

    def report_invalid_class_id_value(self, value):
        self._report("class-id has invalid value: '{}'".format(value))

    def report_class_id_change(self, prev_value, value):
        self._report("class-id changes from '{}' to '{}'".format(prev_value, value))

    def report_no_move(self):
        self._report("Bounding box has the same position as on the previous frame", self.severity.WARNING)

    def report_large_jump(self):
        self._report("Bounding box jumps too much from the position on the previous frame", self.severity.WARNING)

    def report_track_id_non_consecutive(self, ids):
        self._report("track-id values are not consecutive: {}".format(', '.join(sorted(ids))), self.severity.WARNING)
