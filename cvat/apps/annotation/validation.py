import io
from itertools import groupby

from cvat.apps.annotation.structures import BoundingBox, label_by_class_id


def validate(sequences):
    reporter = ValidationReporter()
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
            for bbox_index, bbox in enumerate(frame.bboxes, start=1):
                reporter.bbox_index = bbox_index

                if bbox.track_id in frame_track_ids:
                    duplicated_track_ids.add(bbox.track_id)
                frame_track_ids.add(bbox.track_id)
                sequence_track_ids.add(bbox.track_id)

                _validate_coordinates(bbox, reporter)
                _validate_attributes(bbox, reporter)
                _validate_class_immutability(bbox, class_id_by_track_id, reporter)
                _validate_position_change(bbox, previous_frame, jump_threshold=2, reporter=reporter)

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
    previous_bbox = previous_frame and previous_frame.bbox_by_track_id.get(bbox.track_id)
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


class ValidationReporter:
    def __init__(self):
        self.sequence = None
        self.frame = None
        self.frame_index = None
        self.bbox_index = None
        self._violations = []
        self._frames_count_by_sequence = {}

    def has_violations(self):
        return len(self._violations) > 0

    def write_text_report(self, file):
        data = self.get_json_report()
        for sequence in data['violations']:
            file.write("Sequence {}:\n".format(sequence["name"]))
            for seq_message in sequence["messages"]:
                file.write("\t\t{}\n".format(seq_message))
            for frame in sequence["frames"]:
                file.write("\tFrame {}:\n".format(frame["name"]))
                for frame_message in frame["messages"]:
                    file.write("\t\t{}\n".format(frame_message))
                for box in frame["boxes"]:
                    for message in box["messages"]:
                        file.write("\t\tBox {}: {}\n".format(box["index"], message))
        file.write("Frame counts per sequence:\n")
        for sequence, count in data['counts']['perSequence'].items():
            file.write("\t{}: {}\n".format(sequence, count))
        file.write("Total frames: {}\n".format(data['counts']['total']))

    def get_text_report(self):
        buffer = io.StringIO()
        self.write_text_report(buffer)
        return buffer.getvalue()

    def get_json_report(self):
        violations = _group_violations(self._violations)
        counts = _serialize_counts(self._frames_count_by_sequence)
        return dict(violations=violations, counts=counts)

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
        self._report("Bounding box has the same position as on the previous frame")

    def report_large_jump(self):
        self._report("Bounding box jumps too much from the position on the previous frame")

    def report_track_id_non_consecutive(self, ids):
        self._report("track-id values are not consecutive: {}".format(', '.join(sorted(ids))))

    def count_frame(self, sequence_name):
        self._frames_count_by_sequence[sequence_name] = self._frames_count_by_sequence.get(sequence_name, 0) + 1

    def _report(self, message):
        frame_name = self.frame
        if self.frame_index is not None:
            index = "({})".format(self.frame_index)
            index = index.rjust(6, ' ')
            frame_name = "{}{}".format(frame_name, index)
        self._violations.append((self.sequence, frame_name, self.bbox_index, message))


def _group_violations(data):
    return [_serialize_sequence(s_data, s_name) for s_name, s_data in groupby(data, key=lambda r: r[0])]


def _serialize_sequence(seq_data, seq_name):
    result = {"name": seq_name, "messages": [], "frames": []}
    for frame_name, frame_data in groupby(seq_data, key=lambda r: r[1]):
        if frame_name:
            result["frames"].append(_serialize_frame(frame_data, frame_name))
        else:
            result["messages"].extend(e[3] for e in frame_data)
    return result


def _serialize_frame(frame_data, frame_name):
    result = {"name": frame_name, "messages": [], "boxes": []}
    for box_index, box_data in groupby(frame_data, key=lambda r: r[2]):
        if box_index:
            result["boxes"].append(_serialize_box(box_data, box_index))
        else:
            result["messages"].extend(e[3] for e in box_data)
    return result


def _serialize_box(box_data, box_index):
    return {"index": box_index, "messages": [e[3] for e in box_data]}


def _serialize_counts(_frames_count_by_sequence):
    per_sequence = _frames_count_by_sequence.copy()
    total = sum(count for count in per_sequence.values())
    return {'total': total, 'perSequence': per_sequence}
