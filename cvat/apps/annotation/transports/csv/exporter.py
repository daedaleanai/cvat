import csv
import shutil
import zipfile
import io
from pathlib import Path


class CsvDirectoryExporter:
    def __init__(self, base_dir):
        self._base_dir_path = Path(base_dir)
        if self._base_dir_path.exists():
            shutil.rmtree(str(self._base_dir_path))

    def begin_frame(self, frame_name, sequence_name):
        path = '{}/{}_y.csv'.format(sequence_name, frame_name)
        return FrameFileWriter(self._base_dir_path / path)


class CsvZipExporter:
    def __init__(self, file_object):
        self._archive = zipfile.ZipFile(file_object, 'w')

    def __enter__(self):
        self._archive.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._archive.__exit__(exc_type, exc_val, exc_tb)

    def begin_frame(self, frame_name, sequence_name):
        path = '{}/{}_y.csv'.format(sequence_name, frame_name)
        return FrameZipWriter(self._archive, path)


class BaseWriter:
    def write_bbox(self, bbox):
        row = (_ff(bbox.left), _ff(bbox.top), _ff(bbox.right), _ff(bbox.bottom), bbox.class_id, bbox.track_id)
        self._writer.writerow(row)

    def write_runway(self, runway):
        self._writer.writerow((
            runway.id,
            int(runway.full_visible),
            *runway.start_left.as_row(),
            *runway.start_right.as_row(),
            *runway.end_left.as_row(),
            *runway.end_right.as_row(),
            *runway.threshold_left.as_row(),
            *runway.threshold_right.as_row(),
        ))


class FrameZipWriter(BaseWriter):
    def __init__(self, archive, annotation_path):
        self._path = str(annotation_path)
        self._archive = archive
        self._file = io.StringIO(newline="")
        self._writer = csv.writer(self._file, lineterminator="\n")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._archive.writestr(self._path, self._file.getvalue())


class FrameFileWriter(BaseWriter):
    def __init__(self, file_path):
        self._path = Path(file_path)
        self._file = io.StringIO(newline="")
        self._writer = csv.writer(self._file, lineterminator="\n")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(self._file.getvalue())


def _ff(value):
    return "{0:.6f}".format(value)
