from ..handler import TaskHandler
from .validation import validate, VlsLinesValidationReporter
from .persistence import csv, cvat


class VlsLinesTaskHandler(TaskHandler):
    reporter_class = VlsLinesValidationReporter

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
