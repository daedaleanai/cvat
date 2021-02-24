import csv as pycsv
from collections import OrderedDict

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

    def get_extra_data(self, task):
        task_name = guess_task_name(task.name)
        scenario_files = list(settings.INCOMING_TASKS_ROOT.joinpath(task_name).glob("spo*.csv"))
        if len(scenario_files) != 1:
            return None
        scenario_file = scenario_files[0]
        reader = pycsv.reader(scenario_file.open('rt', newline=''), lineterminator="\n")
        result = {}
        for row in reader:
            sequence_name, record_name, start, end, camera, target_recording, target_type = row
            record_a, record_b = record_name.split('/')
            entry = [
                ("Record #1", record_a),
                ("Record #2", record_b),
                ("Start", start),
                ("End", end),
                ("Camera index", camera),
            ]
            if target_type:
                entry.append(("Target type", target_type))
            if target_recording:
                entry.append(("Target recording", target_recording))
            result[sequence_name] = entry

        track_files = settings.INCOMING_TASKS_ROOT.joinpath(task_name).glob("spo*/tracks/*.csv")
        for track_file in track_files:
            sequence_name = track_file.stem
            track_reader = pycsv.reader(track_file.open('rt', newline=''), lineterminator="\n")
            tracks = [tid for tid, _, _ in track_reader]
            tracks = ", ".join(tracks)
            entry = result.get(sequence_name)
            if entry:
                entry.append(("Track", tracks))

        return {k: OrderedDict(v) for k, v in result.items()}

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
