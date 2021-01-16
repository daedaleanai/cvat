import io
from itertools import groupby
from enum import IntEnum

from cvat.apps.engine.utils import natural_order


class Severity(IntEnum):
    WARNING = 30
    ERROR = 40


class BaseValidationReporter:
    severity = Severity
    object_name = None

    def __init__(self):
        self.sequence = None
        self.frame = None
        self.frame_index = None
        self.object_index = None
        self._violations = []
        self._frames_count_by_sequence = {}

    def begin_frame(self, sequence, frame, frame_index=None):
        self.sequence = sequence
        self.frame = frame
        self.frame_index = frame_index

    def has_violations(self, severity=Severity.ERROR):
        return any(True for *_, sev in self._violations if sev >= severity)

    def write_text_report(self, file, severity=Severity.ERROR):
        data = self.get_json_report(severity)
        for sequence in data['violations']:
            file.write("Sequence {}:\n".format(sequence["name"]))
            for seq_message in sequence["messages"]:
                file.write("\t\t{}\n".format(seq_message))
            for frame in sequence["frames"]:
                file.write("\tFrame {}:\n".format(frame["name"]))
                for frame_message in frame["messages"]:
                    file.write("\t\t{}\n".format(frame_message))
                for obj in frame["objects"]:
                    for message in obj["messages"]:
                        file.write("\t\t{} {}: {}\n".format(self.object_name, obj["index"], message))
        file.write("Frame counts per sequence:\n")
        count_per_sequence = data['counts']['perSequence'].items()
        count_per_sequence = sorted(count_per_sequence, key=lambda e: natural_order(e[0]))
        for sequence, count in count_per_sequence:
            file.write("\t{}: {}\n".format(sequence, count))
        file.write("Total frames: {}\n".format(data['counts']['total']))

    def get_text_report(self, severity=Severity.ERROR):
        buffer = io.StringIO()
        self.write_text_report(buffer, severity)
        return buffer.getvalue()

    def get_json_report(self, severity=Severity.ERROR):
        violations = _group_violations(self._violations, severity)
        counts = _serialize_counts(self._frames_count_by_sequence)
        return dict(violations=violations, counts=counts)

    def count_frame(self, sequence_name):
        self._frames_count_by_sequence[sequence_name] = self._frames_count_by_sequence.get(sequence_name, 0) + 1

    @property
    def frame_name(self):
        frame_name = self.frame
        if self.frame_index is not None:
            index = "({})".format(self.frame_index)
            index = index.rjust(6, ' ')
            frame_name = "{}{}".format(frame_name, index)
        return frame_name

    def _report_sequence_message(self, message, severity=Severity.ERROR):
        self._violations.append((self.sequence, None, None, message, severity))

    def _report(self, message, severity=Severity.ERROR):
        self._violations.append((self.sequence, self.frame_name, self.object_index, message, severity))


def _group_violations(data, severity):
    data = [item for item in data if item[-1] >= severity]
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
    result = {"name": frame_name, "messages": [], "objects": []}
    for object_index, object_data in groupby(frame_data, key=lambda r: r[2]):
        if object_index:
            result["objects"].append(_serialize_object(object_data, object_index))
        else:
            result["messages"].extend(e[3] for e in object_data)
    return result


def _serialize_object(object_data, object_index):
    return {"index": object_index, "messages": [e[3] for e in object_data]}


def _serialize_counts(_frames_count_by_sequence):
    per_sequence = _frames_count_by_sequence.copy()
    total = sum(count for count in per_sequence.values())
    return {'total': total, 'perSequence': per_sequence}
