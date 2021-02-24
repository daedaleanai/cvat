import csv as pycsv
from collections import OrderedDict
from itertools import groupby

from django.conf import settings

from ..handler import TaskHandler
from .validation import validate, VlsLinesValidationReporter
from .persistence import csv, cvat
from ...utils import guess_task_name


class VlsLinesTaskHandler(TaskHandler):
    reporter_class = VlsLinesValidationReporter

    def get_extra_data(self, task):
        task_name = guess_task_name(task.name)
        scenario_files = list(settings.INCOMING_TASKS_ROOT.joinpath(task_name).glob("vls*.csv"))
        if len(scenario_files) != 1:
            return None
        scenario_file = scenario_files[0]
        reader = pycsv.reader(scenario_file.open('rt', newline=''), lineterminator="\n")
        result = {}
        rows = list(reader)
        rows = sorted(rows, key=lambda r: r[0:5])
        rows = groupby(rows, key=lambda r: r[0:5])
        for key, group in rows:
            group = list(group)
            sequence_name, record_name, start, end, camera = key
            record_a, record_b = record_name.split('/')
            entry = [
                ("Record #1", record_a),
                ("Record #2", record_b),
                ("Start", start),
                ("End", end),
                ("Camera index", camera),
            ]
            if len(group) == 1:
                *_, runway_id, runway_info = group[0]
                entry.append(("Runway info", runway_info))
                entry.append(("Runway ID", runway_id))
            else:
                for i, row in enumerate(group, start=1):
                    *_, runway_id, runway_info = row
                    entry.append(("Runway #{} info".format(i), runway_info))
                    entry.append(("Runway #{} ID".format(i), runway_id))
            result[sequence_name] = OrderedDict(entry)
        return result

    def validate(self, sequences, **kwargs):
        return validate(sequences, self.reporter, **kwargs)

    def _iterate_cvat_objects(self, reader):
        return cvat.iterate_runways(reader, self.reporter)

    def _iterate_csv_objects(self, reader):
        return csv.iterate_runways(reader, self.reporter)

    def _write_cvat_object(self, object, writer):
        cvat.write_runway(object, writer)

    def _write_csv_object(self, object, writer):
        csv.write_runway(object, writer)
