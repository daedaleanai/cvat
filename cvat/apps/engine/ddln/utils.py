import datetime
import itertools
import re
from pathlib import PurePath

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


def get_annotation_request_id(task_name):
    task_dir = settings.INCOMING_TASKS_ROOT / task_name
    ddln_id_files = [*task_dir.glob("spo_*/ddln_id"), *task_dir.glob("vls_*/ddln_id")]
    if len(ddln_id_files) != 1:
        return None
    return ddln_id_files[0].read_text().strip()


def get_sequence_id_mapping(task_name):
    task_dir = settings.INCOMING_TASKS_ROOT / task_name
    # it's ok that spo_* and vls_* files get into the dict, they won't be accessed later
    return {f.parent.name: f.read_text().strip() for f in task_dir.glob("*/ddln_id")}


class DdlnYamlWriter:
    def __init__(self, task_name, add_merger_info=True):
        self.task_name = guess_task_name(task_name)
        self.annotation_request_id = get_annotation_request_id(self.task_name)
        self.id_by_seq_name = get_sequence_id_mapping(self.task_name)
        self._add_merger_info = add_merger_info

    def get_warnings(self, sequence_names=()):
        warnings = []
        if not self.annotation_request_id:
            warnings.append("Failure while obtaining annotation request id")
        if not all(name in self.id_by_seq_name for name in sequence_names):
            warnings.append("Failure while getting sequence to dataset-id mapping")
        return warnings

    def write(self, file, rejected_frames=None, date=None):
        if date is None:
            date = datetime.date.today()
        curr_date = date.isoformat()
        annotation_request_id = self.annotation_request_id or ''
        group = settings.ANNOTATION_TEAM
        map_file = "task_mapping.csv"
        merger_info = self._format_merger_info()
        invalid_data = self._format_invalid_data(rejected_frames)

        yml_data = _YML_TEMPLATE.format(
            ddln_id=annotation_request_id,
            curr_date=curr_date,
            group=group,
            map_file=map_file,
            task_name=self.task_name,
            merger_info=merger_info,
            invalid_data=invalid_data,
        )
        file.write(yml_data)

    def _format_merger_info(self):
        merger_version = settings.EXP_DEVTOOLS_HASH
        return _MERGER_INFO_TEMPLATE.format(merger_version=merger_version)

    def _format_invalid_data(self, invalid_frames):
        if not invalid_frames:
            return ""
        return "".join(self._format_invalid_sequence(seq, frames) for seq, frames in invalid_frames.items())

    def _format_invalid_sequence(self, sequence_name, frames):
        dataset_id = self.id_by_seq_name.get(sequence_name, "### UNKNOWN ###")
        frame_rows = "".join("    frame: {}\n".format(f) for f in frames)
        return _INVALID_SEQUENCE_TEMPLATE.format(dataset_id=dataset_id, frame_rows=frame_rows)


_YML_TEMPLATE = """sources:
  - {ddln_id}
date: {curr_date}
team:
  - group: {group}
  - mapping: {map_file}
phabricator: {task_name}
tool:
  - name: CVAT
    version: 2.3
{merger_info}invalid:
{invalid_data}comment:
quality:
recommendations:
"""

_MERGER_INFO_TEMPLATE = """
  - name: merge tool https://git-ng.daedalean.ai/daedalean/exp-devtools/src/branch/master/annotations/multi/process_annotations_msq.py
    version: {merger_version}
""".lstrip('\n')

_INVALID_SEQUENCE_TEMPLATE = """  - dataset_id:  {dataset_id}
{frame_rows}    reason: no agreement
"""
