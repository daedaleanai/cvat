import csv
import io
import re
import shutil
import zipfile
from pathlib import Path


class CsvDirectoryExporter:
    def __init__(self, base_dir, clear_if_exists=True):
        self._base_dir_path = Path(base_dir)
        if clear_if_exists and self._base_dir_path.exists():
            shutil.rmtree(str(self._base_dir_path))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

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

    def get_archive(self):
        return self._archive


class FrameZipWriter:
    def __init__(self, archive, annotation_path):
        self._path = str(annotation_path)
        self._archive = archive
        self._file = io.StringIO(newline="")
        self._writer = csv.writer(self._file, lineterminator="\n")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._archive.writestr(self._path, self._file.getvalue())


class FrameFileWriter:
    def __init__(self, file_path):
        self._path = Path(file_path)
        self._file = io.StringIO(newline="")
        self._writer = csv.writer(self._file, lineterminator="\n")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(self._file.getvalue())


class CsvZipImporter:
    def __init__(self, file_object):
        self._archive = zipfile.ZipFile(file_object, "r")

    def iterate_frames(self):
        for path in self._archive.namelist():
            match = _filename_regex.match(path)
            if not match:
                continue
            sequence_name, frame_name = match.groups()
            yield FrameReader(self._archive.open(path), frame_name, sequence_name)


class CsvDirectoryImporter:
    def __init__(self, directory_path):
        self._path = Path(directory_path)

    def iterate_frames(self):
        for path in self._path.glob('*/*_y.csv'):
            short_path = str(path.relative_to(self._path))
            match = _filename_regex.match(short_path)
            if not match:
                continue
            sequence_name, frame_name = match.groups()
            yield FrameReader(path.open('rb'), frame_name, sequence_name)


class FrameReader:
    def __init__(self, file, frame_name, sequence_name):
        self.name = frame_name
        self.sequence_name = sequence_name
        self._file = io.TextIOWrapper(file, newline="")
        self._reader = csv.reader(self._file, lineterminator="\n")


_filename_regex = re.compile(r"(.*)/(.*)_y.csv")
