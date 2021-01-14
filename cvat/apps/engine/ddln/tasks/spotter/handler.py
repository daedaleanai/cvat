from django.conf import settings

from cvat.apps.engine.ddln.utils import guess_task_name
from ..handler import TaskHandler
from .hints import load_hints
from .validation import validate, SpotterValidationReporter
from .persistence import csv, cvat


class SpotterTaskHandler(TaskHandler):
    reporter_class = SpotterValidationReporter

    def finalize_task_creation(self, task):
        super().finalize_task_creation(task)
        task_name = guess_task_name(task.name)
        hints_dir = settings.INCOMING_TASKS_ROOT / task_name / "hints"
        if hints_dir.exists():
            load_hints(hints_dir, task)

    def validate(self, sequences, **kwargs):
        return validate(sequences, self.reporter, **kwargs)

    def _iterate_cvat_objects(self, reader):
        return cvat.iterate_bboxes(reader)

    def _iterate_csv_objects(self, reader):
        return csv.iterate_bboxes(reader)

    def _write_cvat_object(self, object, writer):
        cvat.write_bbox(object, writer)

    def _write_csv_object(self, object, writer):
        csv.write_bbox(object, writer)
