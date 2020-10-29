import json
import logging
import shutil
from pathlib import Path
from types import SimpleNamespace

import yaml
from django.db import transaction
from django.conf import settings
from rest_framework import serializers

from cvat.apps.annotation.transports.csv import CsvDirectoryExporter
from cvat.apps.annotation.transports.cvat import CVATImporter

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


def accept_segments(task, file_path, segments):
    root_dir = Path(file_path)
    sequences = [s.sequence_name for s in segments]
    _move_accepted_sequences(root_dir, sequences)
    _update_invalid_frames_yaml_file(task, segments, root_dir / "invalid.yaml")
    _remove_archive_file(file_path)


def _move_accepted_sequences(root_dir, sequences):
    rejected_dir = root_dir / "Rejected_annotation_output"
    accepted_dir = root_dir / "Annotation_output"

    for sequence_name in sequences:
        dest_dir = accepted_dir / sequence_name
        src_dir = rejected_dir / sequence_name
        dest_dir.mkdir(exist_ok=True)

        for src_file in src_dir.iterdir():
            dest_file = dest_dir / src_file.relative_to(src_dir)
            src_file.rename(dest_file)

        src_dir.rmdir()

    if len(list(rejected_dir.iterdir())) == 0:
        rejected_dir.rmdir()


def _update_invalid_frames_yaml_file(task, segments, file_path):
    """Remove accepted sequences from invalid frames yaml file."""
    accepted_sequences = {s.sequence_name for s in segments}
    yaml_writer = DdlnYamlWriter(task.name)
    seq_name_by_ddln_id = {ddln_id: seq for seq, ddln_id in yaml_writer.id_by_seq_name.items()}
    rejected_frames = _load_rejected_frames(file_path, seq_name_by_ddln_id)
    still_rejected_frames = {seq: frames for seq, frames in rejected_frames.items() if seq not in accepted_sequences}
    yaml_writer.write_invalid_frames(file_path.open('wt'), still_rejected_frames)


def _load_rejected_frames(file_path, seq_name_by_ddln_id):
    data = yaml.load(file_path.open('rt'))
    rejected_frames = {}
    if not data:
        return rejected_frames
    for entry in data:
        ddln_id = entry['dataset_id']
        sequence_name = seq_name_by_ddln_id.get(ddln_id, '### UNKNOWN ###')
        frame = entry['frame']
        if sequence_name not in rejected_frames:
            rejected_frames[sequence_name] = []
        rejected_frames[sequence_name].append(frame)
    return rejected_frames


class FailedAssignmentError(Exception):
    """Error raised when proper assignees cannot be found for some of the segments"""
    def __init__(self, failed_segments):
        self.failed_segments = failed_segments


def merge(task_id, file_path, acceptance_score):
    task = Task.objects.get(pk=task_id)

    root_dir = Path(file_path)
    if root_dir.exists():
        shutil.rmtree(str(root_dir))
        _remove_archive_file(file_path)
    root_dir.mkdir()
    versions_dir = root_dir / "Annotation_versions"
    accepted_dir = root_dir / "Annotation_output"
    rejected_dir = root_dir / "Rejected_annotation_output"
    requires_more_dir = root_dir / "Requires_more_annotations"
    logs_dir = root_dir / "Annotation_log"
    for d in [versions_dir, accepted_dir, rejected_dir, requires_more_dir, logs_dir]:
        d.mkdir()
    log_file = logs_dir / "final_merge.log"
    score_file = logs_dir / "final_scores.txt"
    ddln_yaml_file = root_dir / "ddln.yaml"
    invalid_frames_file = root_dir / "invalid.yaml"

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
    yaml_writer.write_metadata(ddln_yaml_file.open("wt"))
    yaml_writer.write_invalid_frames(invalid_frames_file.open("wt"), rejected_frames)
    copy_previous_merge_logs(root_dir, task.times_annotated)

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


def copy_previous_merge_logs(current_merge_dir, times_annotated):
    prev_merge_name = current_merge_dir.name.replace("-x{}".format(times_annotated), "-x{}".format(times_annotated-1))
    prev_merge_dir = current_merge_dir.with_name(prev_merge_name)
    if not prev_merge_dir.exists():
        return
    src_log_file = prev_merge_dir / "Annotation_log" / "final_merge.log"
    dest_log_file = current_merge_dir / "Annotation_log" / "intermediate_merge.log"
    src_score_file = prev_merge_dir / "Annotation_log" / "final_scores.txt"
    dest_score_file = current_merge_dir / "Annotation_log" / "intermediate_scores.txt"
    shutil.copy(str(src_log_file), str(dest_log_file))
    shutil.copy(str(src_score_file), str(dest_score_file))


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


def _remove_archive_file(file_path):
    archive_path = "{}.zip".format(file_path)
    archive_path = Path(archive_path)
    if archive_path.exists():
        archive_path.unlink()


def _dump_version(task, version, target_dir):
    job_selection = dict(version=version, jobs=[])
    importer = CVATImporter.for_task(task.id, job_selection)
    with CsvDirectoryExporter(target_dir) as exporter:
        for frame_reader in importer.iterate_frames():
            with exporter.begin_frame(frame_reader.name, frame_reader.sequence_name) as frame_writer:
                for bbox in frame_reader.iterate_bboxes():
                    frame_writer.write_bbox(bbox)
