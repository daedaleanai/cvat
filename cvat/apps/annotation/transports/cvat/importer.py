from django.contrib.auth.models import AnonymousUser
from django.db import transaction

from cvat.apps.annotation.annotation import Annotation
from cvat.apps.engine.annotation import TaskAnnotation
from cvat.apps.annotation.structures import LabeledBoundingBox
from .utils import parse_frame_name, build_attrs_dict
from . import runway as runway_module


class CVATImporter:
    def __init__(self, annotations, logger=None):
        self._annotations = annotations
        self._logger = logger

    @classmethod
    def for_task(cls, task_id, logger=None):
        with transaction.atomic():
            annotation = TaskAnnotation(task_id, AnonymousUser())
            annotation.init_from_db()

        anno_exporter = Annotation(
            annotation_ir=annotation.ir_data,
            db_task=annotation.db_task,
            scheme='https',
            host='',
        )
        return cls(anno_exporter, logger)

    def iterate_frames(self):
        for frame_annotation in self._annotations.group_by_frame(omit_empty_frames=False):
            frame_name, sequence_name = parse_frame_name(frame_annotation.name)
            frame_index = frame_annotation.frame

            has_empty_placeholder = any(shape.label.lower() == "empty" for shape in frame_annotation.labeled_shapes)
            if has_empty_placeholder:
                yield CVATFrameReader(None, frame_name, sequence_name, frame_index, self._logger)
                continue

            yield CVATFrameReader(frame_annotation, frame_name, sequence_name, frame_index, self._logger)


class CVATFrameReader:
    def __init__(self, frame_annotation, frame_name, sequence_name, index, logger):
        self._frame_annotation = frame_annotation
        self._logger = logger
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

            bbox = LabeledBoundingBox.from_two_corners(xtl, ytl, xbr, ybr, class_id, track_id)
            if source:
                bbox.source = source
                bbox.score = score
            yield bbox

    def get_log_prefix(self):
        if self.index:
            index = self.index
            index = str(index).rjust(6, ' ')
            index = " ({})".format(index)
        else:
            index = ''
        return "seq {!r} frame {!r} {}: ".format(self.sequence_name, self.name, index)

    def iterate_runways(self):
        if not self._frame_annotation:
            return

        self._logger.prefix = self.get_log_prefix()
        try:
            runway = runway_module.parse_points(self._frame_annotation.labeled_shapes)
            if runway:
                visibility_message = runway.validate_visibility()
                if visibility_message:
                    self._logger.log(visibility_message)
                yield runway
        except runway_module.RunwayParseError as e:
            self._logger.log(e.args[0])

        for shape in self._frame_annotation.labeled_shapes:
            if shape.type != "polyline":
                continue
            try:
                runway = runway_module.parse_polyline(shape)
                visibility_message = runway.validate_visibility()
                if visibility_message:
                    self._logger.log(visibility_message)
                yield runway
            except runway_module.RunwayParseError as e:
                self._logger.log(e.args[0])
