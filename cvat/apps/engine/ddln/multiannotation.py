from django.db import transaction

from cvat.apps.engine import models
from cvat.apps.engine.ddln.sequences import extend_assignees


def request_extra_annotation(task, segments, assignees):
    segments_data = [(s, s.length, set(s.get_performers())) for s in segments]

    assignments, failed_segments = extend_assignees(segments_data, assignees)

    if failed_segments:
        raise FailedAssignmentError(failed_segments)

    with transaction.atomic():
        version = task.times_annotated
        for segment, assignee in assignments:
            db_job = models.Job()
            db_job.segment = segment
            db_job.version = version
            db_job.assignee = assignee
            db_job.save()
        task.times_annotated += 1
        task.save()


class FailedAssignmentError(Exception):
    """Error raised when proper assignees cannot be found for some of the segments"""
    def __init__(self, failed_segments):
        self.failed_segments = failed_segments
