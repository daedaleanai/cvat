import csv
import io
import re
import zipfile
from pathlib import PurePath
from types import SimpleNamespace


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


def add_bbox(bbox, frame_id, annotations):
    width = annotations._frame_info[frame_id]["width"]
    height = annotations._frame_info[frame_id]["height"]

    xtl = float(bbox.xtl) * width
    ytl = float(bbox.ytl) * height
    xbr = float(bbox.xbr) * width
    ybr = float(bbox.ybr) * height

    shape = {
        'attributes': [
            annotations.Attribute(
                name='Object_class',
                value=bbox.class_id,
            ),
            annotations.Attribute(
                name='Track_id',
                value=bbox.track_id,
            ),
        ],
        'points': [xtl, ytl, xbr, ybr],
        'frame': frame_id,
        'group': 0,
        'z_order': 0,
        'occluded': False,
        'type': 'rectangle',
        'label': label_by_class_id[bbox.class_id],
    }
    annotations.add_shape(annotations.LabeledShape(**shape))


def build_frame_id_mapping(annotations):
    assert annotations._frame_step == 1
    return {
        parse_frame_name(f.name): f.frame
        for f in annotations.group_by_frame(omit_empty_frames=False)
    }


def parse_frame_name(path):
    image_path = PurePath(path)
    sequence_name = image_path.parents[2].name
    frame_name = image_path.stem
    return frame_name, sequence_name


class FrameReader:
    def __init__(self, file, frame_name, sequence_name):
        self.name = frame_name
        self.sequence_name = sequence_name
        self._file = io.TextIOWrapper(file, newline="")
        self._reader = csv.reader(self._file, lineterminator="\n")

    def iterate_bboxes(self):
        for xtl, ytl, xbr, ybr, class_id, track_id in self._reader:
            yield SimpleNamespace(xtl=xtl, ytl=ytl, xbr=xbr, ybr=ybr, class_id=class_id, track_id=track_id)


label_by_class_id = {
    "1": "Drone",
    "3": "Flying bird",
    "4": "Fixed wing aircraft",
    "5": "Helicopter",
    "100": "Unknown",
}


_filename_regex = re.compile(r"(.*)/(.*)_y.csv")
