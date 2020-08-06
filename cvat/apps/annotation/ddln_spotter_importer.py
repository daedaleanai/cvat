import csv
import io
import re
import zipfile
from pathlib import PurePath, Path
from types import SimpleNamespace

from django.contrib.auth.models import AnonymousUser
from django.db import transaction

from cvat.apps.annotation.annotation import Annotation
from cvat.apps.engine.annotation import TaskAnnotation


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


class CVATImporter:
    def __init__(self, annotations):
        self._annotations = annotations

    @classmethod
    def for_task(cls, task_id):
        with transaction.atomic():
            annotation = TaskAnnotation(task_id, AnonymousUser())
            annotation.init_from_db()

        anno_exporter = Annotation(
            annotation_ir=annotation.ir_data,
            db_task=annotation.db_task,
            scheme='https',
            host='',
        )
        return cls(anno_exporter)

    def iterate_frames(self):
        for frame_annotation in self._annotations.group_by_frame(omit_empty_frames=False):
            frame_name, sequence_name = parse_frame_name(frame_annotation.name)
            frame_index = frame_annotation.frame

            if any(
                shape.label.lower() == "empty" for shape in frame_annotation.labeled_shapes
            ):
                yield CVATFrameReader(None, frame_name, sequence_name, frame_index)
                continue

            yield CVATFrameReader(frame_annotation, frame_name, sequence_name, frame_index)


class CVATFrameReader:
    def __init__(self, frame_annotation, frame_name, sequence_name, index):
        self._frame_annotation = frame_annotation
        self.name = frame_name
        self.sequence_name = sequence_name
        self.index = index

    def iterate_bboxes(self):
        if not self._frame_annotation:
            return
        height = float(self._frame_annotation.height)
        width = float(self._frame_annotation.width)

        for shape in self._frame_annotation.labeled_shapes:
            if shape.type != "rectangle":
                # only bounding box is supported
                continue

            attrs = self._get_attributes(shape)

            class_id = attrs.get("Object_class", "")
            track_id = attrs.get("Track_id", "")
            score = attrs.get("Score")
            source = attrs.get("Source")

            xtl, ytl, xbr, ybr = map(float, shape.points)
            xtl = xtl / width
            ytl = ytl / height
            xbr = xbr / width
            ybr = ybr / height

            yield SimpleNamespace(
                xtl=xtl,
                ytl=ytl,
                xbr=xbr,
                ybr=ybr,
                class_id=class_id,
                track_id=track_id,
                score=score,
                source=source,
            )

    def _get_attributes(self, shape):
        return {a.name: a.value for a in shape.attributes}


def add_bbox(bbox, frame_id, annotations):
    width = annotations._frame_info[frame_id]["width"]
    height = annotations._frame_info[frame_id]["height"]

    xtl = float(bbox.xtl) * width
    ytl = float(bbox.ytl) * height
    xbr = float(bbox.xbr) * width
    ybr = float(bbox.ybr) * height

    attributes = [
        annotations.Attribute(name="Object_class", value=bbox.class_id),
        annotations.Attribute(name="Track_id", value=bbox.track_id),
    ]

    if bbox.score:
        attributes.append(annotations.Attribute(name="Score", value=bbox.score))
    if bbox.source:
        attributes.append(annotations.Attribute(name="Source", value=bbox.source))

    shape = {
        "attributes": attributes,
        "points": [xtl, ytl, xbr, ybr],
        "frame": frame_id,
        "group": 0,
        "z_order": 0,
        "occluded": False,
        "type": "rectangle",
        "label": label_by_class_id[bbox.class_id],
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
        for row in self._reader:
            score, source = None, None
            if len(row) == 8:
                *row, score, source = row
            *points, class_id, track_id = row
            xtl, ytl, xbr, ybr = map(float, points)
            yield SimpleNamespace(
                xtl=xtl,
                ytl=ytl,
                xbr=xbr,
                ybr=ybr,
                class_id=class_id,
                track_id=track_id,
                score=score,
                source=source,
            )


label_by_class_id = {
    "1": "Drone",
    "3": "Flying bird",
    "4": "Fixed wing aircraft",
    "5": "Helicopter",
    "100": "Unknown",
}


_filename_regex = re.compile(r"(.*)/(.*)_y.csv")
