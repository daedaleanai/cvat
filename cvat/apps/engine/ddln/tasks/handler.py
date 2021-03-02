import abc
import csv as pycsv
from collections import defaultdict, OrderedDict

from cvat.apps.engine.utils import natural_order
from .models import Sequence, Frame
from ..transports.cvat import CVATFrameWriter, CVATFrameReader


class TaskHandler(abc.ABC):
    reporter_class = None

    def __init__(self):
        self.reporter = self.reporter_class()

    def load_sequences(self, importer, image_width=None, image_height=None):
        frames_by_sequence_name = defaultdict(list)
        for frame_reader in importer.iterate_frames():
            if not getattr(frame_reader, "image_width", None) and image_width:
                frame_reader.image_width = image_width
            if not getattr(frame_reader, "image_height", None) and image_height:
                frame_reader.image_height = image_height
            frame_index = getattr(frame_reader, "index", None)
            self.begin_frame(frame_reader.sequence_name, frame_reader.name, frame_index)
            frame = Frame(frame_reader.name, list(self.iterate_objects(frame_reader)))
            if hasattr(frame_reader, 'index'):
                frame.index = frame_reader.index
            frames_by_sequence_name[frame_reader.sequence_name].append(frame)

        sequences = []
        for sequence_name, frames in frames_by_sequence_name.items():
            frames.sort(key=lambda f: f.name)
            sequences.append(Sequence(sequence_name, frames))
        sequences.sort(key=lambda s: natural_order(s.name))

        return sequences

    def finalize_task_creation(self, task):
        pass

    def get_extra_info(self, task):
        return None

    def begin_frame(self, sequence, frame, frame_index=None):
        self.reporter.begin_frame(sequence, frame, frame_index)

    def iterate_objects(self, reader):
        if isinstance(reader, CVATFrameReader):
            return self._iterate_cvat_objects(reader)
        return self._iterate_csv_objects(reader)

    def write_object(self, object, writer):
        if isinstance(writer, CVATFrameWriter):
            return self._write_cvat_object(object, writer)
        return self._write_csv_object(object, writer)

    @abc.abstractmethod
    def validate(self, sequences, **kwargs):
        pass

    @abc.abstractmethod
    def _iterate_cvat_objects(self, reader):
        pass

    @abc.abstractmethod
    def _iterate_csv_objects(self, reader):
        pass

    @abc.abstractmethod
    def _write_cvat_object(self, object, writer):
        pass

    @abc.abstractmethod
    def _write_csv_object(self, object, writer):
        pass

    def _get_common_extra_info(self, scenario_file):
        reader = pycsv.reader(scenario_file.open('rt', newline=''), lineterminator="\n")
        result = {}
        for row in reader:
            if len(row) < 5:
                # skip empty or invalid lines to
                continue
            sequence_name, record_name, start, end, camera, *_ = row
            record_a, record_b = record_name.split('/')
            entry = OrderedDict([
                ("Record #1", record_a),
                ("Record #2", record_b),
                ("Start", start),
                ("End", end),
                ("Camera index", camera),
            ])
            result[sequence_name] = entry
        return result

    def _append_per_sequence_info(self, result, sequence_files, fields):
        for file in sequence_files:
            sequence_name = file.stem
            entry = result.get(sequence_name)
            if not entry:
                continue
            rows = list(pycsv.reader(file.open('rt', newline=''), lineterminator="\n"))
            if len(rows) == 1:
                for field, value in zip(fields, rows[0]):
                    entry[field] = value
            else:
                for i, row in enumerate(rows, start=1):
                    for field, value in zip(fields, row):
                        key = "#{} {}".format(i, field)
                        entry[key] = value
