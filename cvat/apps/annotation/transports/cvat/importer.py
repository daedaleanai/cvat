from types import SimpleNamespace

from django.contrib.auth.models import AnonymousUser
from django.db import transaction

from cvat.apps.annotation.annotation import Annotation
from cvat.apps.engine.annotation import TaskAnnotation
from .utils import parse_frame_name, build_attrs_dict


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

            attrs = build_attrs_dict(shape)

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
