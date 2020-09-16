import datetime
import itertools
import re
from pathlib import PurePath, Path

from django.conf import settings

from cvat.apps.engine.utils import natural_order


def parse_frame_name(path):
    image_path = PurePath(path)
    if len(image_path.parents) < 3:
        return path, ''
    sequence_name = image_path.parents[2].name
    frame_name = image_path.stem
    return frame_name, sequence_name


class FrameContainer:
    # both start_frame and stop_frame are inclusive,
    # but boundary is exclusive (i.e. boundary = end_frame + 1)
    def __init__(self, ranges):
        frame_set = set()
        boundaries = []
        for start_frame, stop_frame in ranges:
            boundaries.append(stop_frame + 1)
            segment_frames = range(start_frame, stop_frame + 1)
            frame_set = frame_set.union(segment_frames)
        boundaries.sort()
        self._frame_set = frame_set
        self._boundaries = boundaries

    @classmethod
    def for_jobs(cls, jobs):
        return cls((job.segment.start_frame, job.segment.stop_frame) for job in jobs)

    def contains(self, frame):
        return frame in self._frame_set

    def get_closest_boundary(self, frame):
        for b in self._boundaries:
            if b > frame:
                return b
        raise ValueError("Frame '{}' is greater than any boundary".format(frame))


def write_task_mapping_file(task, file):
    assignment_data = task.get_assignment_data()
    assignment_data.sort(key=lambda row: (row[0], natural_order(row[1])))
    for version, group in itertools.groupby(assignment_data, key=lambda row: row[0]):
        file.write("V{}:\n".format(version + 1))
        for _, sequence_name, annotator_name in group:
            file.write("{}\t{}\n".format(sequence_name, annotator_name or ''))
        file.write("\n")


def guess_task_name(name):
    match = re.search(r"T\d+(?:_\d+)?", name)
    if match:
        return match.group()
    return name


def write_ddln_yaml_file(task_name, file, rejected_frames, date=None, annotation_request_id=None, id_by_seq_name=None):
    if date is None:
        date = datetime.date.today()
    if id_by_seq_name is None:
        id_by_seq_name = get_sequence_id_mapping(task_name)
    if annotation_request_id is None:
        annotation_request_id = get_annotation_request_id(task_name)
    annotation_request_id = annotation_request_id or ''
    group = "msq"
    map_file = "task_mapping.csv"
    curr_date = date.isoformat()
    merger_version = settings.EXP_DEVTOOLS_HASH
    if rejected_frames:
        invalid_data = "".join(_format_invalid_sequence(seq, frames, id_by_seq_name) for seq, frames in rejected_frames.items())
    else:
        invalid_data = ""

    yml_data = YML_TEMPLATE.format(
        ddln_id=annotation_request_id,
        curr_date=curr_date,
        group=group,
        map_file=map_file,
        task_name=task_name,
        merger_version=merger_version,
        invalid_data=invalid_data,
    )
    file.write(yml_data)


def _format_invalid_sequence(sequence_name, frames, id_by_seq_name):
    dataset_id = id_by_seq_name.get(sequence_name, "### UNKNOWN ###")
    frame_rows = "".join("    frame: {}\n".format(f) for f in frames)
    return INVALID_SEQUENCE_TEMPLATE.format(dataset_id=dataset_id, frame_rows=frame_rows)


def get_annotation_request_id(task_name):
    task_dir = _get_task_directory(task_name)
    ddln_id_files = [*task_dir.glob("spo_*/ddln_id"), *task_dir.glob("vls_*/ddln_id")]
    if len(ddln_id_files) != 1:
        return None
    return ddln_id_files[0].read_text().strip()


def get_sequence_id_mapping(task_name):
    task_dir = _get_task_directory(task_name)
    # it's ok that spo_* and vls_* files get into the dict, they won't be accessed later
    return {f.parent.name: f.read_text().strip() for f in task_dir.glob("*/ddln_id")}


def _get_task_directory(task_name):
    base_dir = Path("/home/django/share/incoming")
    return base_dir.joinpath(task_name)


YML_TEMPLATE = """sources:
  - {ddln_id}
date: {curr_date}
team:
  - group: {group}
  - mapping: {map_file}
phabricator: {task_name}
tool:
  - name: CVAT
    version: 2.3
  - name: merge tool https://git-ng.daedalean.ai/daedalean/exp-devtools/src/branch/master/annotations/multi/process_annotations_msq.py
    version: {merger_version}
invalid:
{invalid_data}comment:
quality:
recommendations: """

INVALID_SEQUENCE_TEMPLATE = """  - dataset_id:  {dataset_id}
{frame_rows}    reason: no agreement
"""
