import abc
from collections import defaultdict

from cvat.apps.engine.utils import natural_order
from .models import Sequence, Frame
from ..transports.cvat import CVATFrameWriter, CVATFrameReader


class TaskHandler(abc.ABC):
    reporter_class = None

    def __init__(self):
        self.reporter = self.reporter_class()

    def load_sequences(self, importer):
        frames_by_sequence_name = defaultdict(list)
        for frame_reader in importer.iterate_frames():
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
