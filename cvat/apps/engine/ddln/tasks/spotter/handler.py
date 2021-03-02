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

    def get_extra_info(self, task):
        task_name = guess_task_name(task.name)
        scenario_files = list(settings.INCOMING_TASKS_ROOT.joinpath(task_name).glob("spo*.csv"))
        if len(scenario_files) != 1:
            return None
        scenario_file = scenario_files[0]
        result = self._get_common_extra_info(scenario_file)
        track_files = settings.INCOMING_TASKS_ROOT.joinpath(task_name).glob("spo*/tracks/*.csv")
        self._append_per_sequence_info(result, track_files, ['Track ID', 'target', 'type'])
        return result

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
