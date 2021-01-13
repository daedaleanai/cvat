import csv
from pathlib import Path

from ..models import Hint


class HintsCsvImporter:
    def __init__(self, directory_path):
        self._path = Path(directory_path)

    def iterate_sequences(self):
        for seq_dir in self._path.iterdir():
            if not seq_dir.is_dir(): continue
            yield HintsSequenceReader(seq_dir)


class HintsSequenceReader:
    def __init__(self, sequence_directory):
        self._path = sequence_directory
        self.sequence_name = self._path.stem

    def iterate_frames(self):
        for path in sorted(self._path.glob('*.csv')):
            frame_name = path.stem.rjust(20, '0')
            yield HintsFrameReader(path.open('rt', newline=''), frame_name, self.sequence_name)


class HintsFrameReader:
    def __init__(self, file, frame_name, sequence_name):
        self.name = frame_name
        self.sequence_name = sequence_name
        self._file = file
        self._reader = csv.reader(self._file, lineterminator="\n")
        next(self._reader)

    def iterate_hints(self):
        for row in self._reader:
            id, x, y, type, distance, vertical_distance, velocity = row
            x = float(x)
            y = float(y)
            distance = float(distance)
            vertical_distance = float(vertical_distance)
            velocity = float(velocity)
            hint = Hint(x, y, id, type, distance, vertical_distance, velocity)
            yield hint
