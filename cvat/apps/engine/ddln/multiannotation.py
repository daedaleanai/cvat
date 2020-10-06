import json
import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from django.db import transaction
from django.conf import settings
from rest_framework import serializers

from cvat.apps.annotation.transports.csv import CsvDirectoryExporter
from cvat.apps.annotation.transports.cvat import CVATImporter
from cvat.apps.dataset_manager.util import make_zip_archive

from cvat.apps.engine import models
from cvat.apps.engine.ddln.inventory_client import record_extra_annotation_creation, record_task_validation
from cvat.apps.engine.ddln.sequences import extend_assignees
from cvat.apps.engine.ddln.utils import (
    write_task_mapping_file,
    DdlnYamlWriter,
)
from cvat.apps.engine.models import Task, Segment
from cvat.apps.engine.utils import natural_order
from merge_annotations import merge_annotations

logger = logging.getLogger(__name__)
ignored_logger = logger.getChild("ignored")


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
    record_extra_annotation_creation(task, assignments, version)


class FailedAssignmentError(Exception):
    """Error raised when proper assignees cannot be found for some of the segments"""
    def __init__(self, failed_segments):
        self.failed_segments = failed_segments


def merge(task_id, file_path, acceptance_score):
    task = Task.objects.get(pk=task_id)

    with TemporaryDirectory() as root_dir:
        root_dir = Path(root_dir)
        versions_dir = root_dir / "Annotation_versions"
        accepted_dir = root_dir / "Annotation_output"
        rejected_dir = root_dir / "Rejected_annotation_output"
        requires_more_dir = root_dir / "Requires_more_annotations"
        logs_dir = root_dir / "Annotation_log"
        for d in [versions_dir, accepted_dir, rejected_dir, requires_more_dir, logs_dir]:
            d.mkdir()
        log_file = logs_dir / "merge.log"
        score_file = logs_dir / "scores.txt"
        ddln_yaml_file = root_dir / "ddln.yaml"

        annotation_dirs = []
        extra_annotation_dir = None
        for version in range(task.times_annotated):
            version_dir = versions_dir.joinpath("V{}".format(version + 1))
            version_dir.mkdir()

            _dump_version(task, version, version_dir)

            is_extra_annotation = version == 3
            if is_extra_annotation:
                extra_annotation_dir = version_dir
            else:
                annotation_dirs.append(version_dir)

        options = SimpleNamespace(
            logger=ignored_logger,
            log_file=log_file,
            extra_annotation_dir=extra_annotation_dir,
            acceptance_score=acceptance_score,
            visualize_file=None,
            score_file=score_file,
            track_matching_threshold=0.2,
        )
        merge_logger = merge_annotations(annotation_dirs, accepted_dir, rejected_dir, requires_more_dir, options)
        rejected_frames = merge_logger.get_rejected_frames()
        incomplete_frames = merge_logger.get_incomplete_frames()

        write_task_mapping_file(task, root_dir.joinpath("task_mapping.csv").open("wt"))
        yaml_writer = DdlnYamlWriter(task.name)
        yaml_writer.write(ddln_yaml_file.open("wt"), rejected_frames)
        make_zip_archive(str(root_dir), file_path)

    segments = Segment.objects.with_sequence_name().filter(task_id=task.id).prefetch_related('job_set__assignee')
    serializer_context = dict(
        dataset_id_by_sequence_name=yaml_writer.id_by_seq_name,
        rejected_frames=rejected_frames,
        incomplete_frames=incomplete_frames
    )
    segments_serializer = MergeResultSerializer(segments, many=True, context=serializer_context)

    warnings = yaml_writer.get_warnings(s.sequence_name for s in segments)

    segments_data = sorted(segments_serializer.data, key=lambda e: natural_order(e['sequence_name']))
    data = dict(warnings=warnings, segments=segments_data)
    json.dump(data, open(file_path + '.json', 'w'))
    record_task_validation(task, settings.EXP_DEVTOOLS_HASH)


class MergeResultSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    sequence_name = serializers.CharField()
    dataset_id = serializers.SerializerMethodField()
    rejected_frames_count = serializers.SerializerMethodField()
    incomplete_frames_count = serializers.SerializerMethodField()
    annotators = serializers.SerializerMethodField()

    def get_dataset_id(self, segment):
        dataset_id_by_sequence_name = self.context['dataset_id_by_sequence_name']
        return dataset_id_by_sequence_name.get(segment.sequence_name, '')

    def get_rejected_frames_count(self, segment):
        rejected_frames = self.context['rejected_frames']
        if segment.sequence_name in rejected_frames:
            return len(rejected_frames[segment.sequence_name])
        return 0

    def get_incomplete_frames_count(self, segment):
        incomplete_frames = self.context['incomplete_frames']
        if segment.sequence_name in incomplete_frames:
            return len(incomplete_frames[segment.sequence_name])
        return 0

    def get_annotators(self, segment):
        return [job.assignee.username for job in segment.job_set.all() if job.assignee]


def _dump_version(task, version, target_dir):
    job_selection = dict(version=version, jobs=[])
    importer = CVATImporter.for_task(task.id, job_selection)
    with CsvDirectoryExporter(target_dir) as exporter:
        for frame_reader in importer.iterate_frames():
            with exporter.begin_frame(frame_reader.name, frame_reader.sequence_name) as frame_writer:
                for bbox in frame_reader.iterate_bboxes():
                    frame_writer.write_bbox(bbox)
