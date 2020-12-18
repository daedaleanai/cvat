from django.contrib.auth.models import AnonymousUser
from django.db import transaction

from ..utils import parse_frame_name


class CVATExporter:
    def __init__(self, annotations):
        self._annotations = annotations
        self._frame_id_by_names = self._build_frame_id_mapping(annotations)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def begin_frame(self, frame_name, sequence_name):
        frame_id = self._frame_id_by_names[frame_name, sequence_name]
        return CVATFrameWriter(self._annotations, frame_id)

    def _build_frame_id_mapping(self, annotations):
        assert annotations._frame_step == 1
        return {
            parse_frame_name(f.name): f.frame
            for f in annotations.group_by_frame(omit_empty_frames=False)
        }


class CVATFrameWriter:
    def __init__(self, annotations, frame_id):
        self._annotations = annotations
        self._frame_id = frame_id

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @property
    def image_width(self):
        return self._annotations._frame_info[self._frame_id]["width"]

    @property
    def image_height(self):
        return self._annotations._frame_info[self._frame_id]["height"]



class CVATImporter:
    def __init__(self, annotations):
        self._annotations = annotations

    @classmethod
    def for_task(cls, task_id, job_selection=None):
        from cvat.apps.annotation.annotation import Annotation
        from cvat.apps.engine.annotation import TaskAnnotation

        with transaction.atomic():
            annotation = TaskAnnotation(task_id, AnonymousUser(), job_selection)
            annotation.init_from_db()

        anno_exporter = Annotation(
            annotation_ir=annotation.ir_data,
            db_task=annotation.db_task,
            scheme='https',
            host='',
            frame_container=annotation._frame_container,
        )
        return cls(anno_exporter)

    def iterate_frames(self):
        for frame_annotation in self._annotations.group_by_frame(omit_empty_frames=False):
            frame_name, sequence_name = parse_frame_name(frame_annotation.name)
            frame_index = frame_annotation.frame

            has_empty_placeholder = any(shape.label.lower() == "empty" for shape in frame_annotation.labeled_shapes)
            if has_empty_placeholder:
                yield CVATFrameReader(None, frame_name, sequence_name, frame_index)
                continue

            yield CVATFrameReader(frame_annotation, frame_name, sequence_name, frame_index)


class CVATFrameReader:
    def __init__(self, frame_annotation, frame_name, sequence_name, index):
        self._frame_annotation = frame_annotation
        self.name = frame_name
        self.sequence_name = sequence_name
        self.index = index

    @property
    def image_width(self):
        return self._frame_annotation.width

    @property
    def image_height(self):
        return self._frame_annotation.height
