from ..handler import TaskHandler
from .validation import validate, SpotterValidationReporter
from .persistence import csv, cvat


class SpotterTaskHandler(TaskHandler):
    reporter_class = SpotterValidationReporter

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
