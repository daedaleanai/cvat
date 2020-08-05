import csv
import io
import re
import zipfile
from pathlib import Path

from cvat.apps.annotation.structures import LabeledBoundingBox, Runway, RunwayPoint


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

    def iterate_bboxes(self):
        for row in self._reader:
            score, source = None, None
            if len(row) == 8:
                *row, score, source = row
            *points, class_id, track_id = row
            xtl, ytl, xbr, ybr = map(float, points)
            bbox = LabeledBoundingBox.from_two_corners(xtl, ytl, xbr, ybr, class_id, track_id)
            if source:
                bbox.source = source
                bbox.score = score
            yield bbox

    def iterate_runways(self):
        for row in self._reader:
            runway_id, full_visible, *pts_data = row
            full_visible = bool(int(full_visible))
            assert len(pts_data) == 18  # 6 points, each point having 3 values
            start_left, start_right = RunwayPoint.from_row(pts_data[0:3]), RunwayPoint.from_row(pts_data[3:6])
            end_left, end_right = RunwayPoint.from_row(pts_data[6:9]), RunwayPoint.from_row(pts_data[9:12])
            threshold_left, threshold_right = RunwayPoint.from_row(pts_data[12:15]), RunwayPoint.from_row(pts_data[15:18])
            yield Runway(runway_id, full_visible, start_left, start_right, end_left, end_right, threshold_left, threshold_right)


_filename_regex = re.compile(r"(.*)/(.*)_y.csv")
