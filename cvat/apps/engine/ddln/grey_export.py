import logging
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from django.conf import settings

from cvat.apps.annotation.structures import load_sequences
from cvat.apps.annotation.transports.cvat import CVATImporter
from cvat.apps.annotation.transports.csv import CsvDirectoryExporter, CsvDirectoryImporter
from cvat.apps.annotation.validation import validate
from cvat.apps.engine.ddln.utils import write_task_mapping_file, DdlnYamlWriter, guess_task_name

logger = logging.getLogger(__name__)


class ExportError(Exception):
    pass


def export_single_annotation(task):
    task_name = guess_task_name(task.name)
    destination_dir = settings.OUTGOING_TASKS_ROOT / task_name
    if destination_dir.exists():
        raise ExportError("Task has already been exported")

    with TemporaryDirectory() as root_dir:
        root_dir = Path(root_dir)
        task_mapping_file = root_dir / 'task_mapping.csv'
        ddln_yaml_file = root_dir / 'ddln.yaml'

        importer = CVATImporter.for_task(task.id)
        with CsvDirectoryExporter(root_dir, clear_if_exists=False) as exporter:
            for frame_reader in importer.iterate_frames():
                with exporter.begin_frame(frame_reader.name, frame_reader.sequence_name) as frame_writer:
                    for bbox in frame_reader.iterate_bboxes():
                        frame_writer.write_bbox(bbox)

        sequences = load_sequences(CsvDirectoryImporter(root_dir))
        reporter = validate(sequences)
        if reporter.has_violations(reporter.severity.ERROR):
            message = reporter.get_text_report(reporter.severity.ERROR)
            raise ExportError(message)

        write_task_mapping_file(task, task_mapping_file.open('w'))
        yaml_writer = DdlnYamlWriter(task.name)
        yaml_writer.write(ddln_yaml_file.open('wt'))
        warnings = yaml_writer.get_warnings()
        if warnings:
            message = ", ".join(warnings)
            raise ExportError(message)

        try:
            ddln_id = calculate_ddln_id(root_dir, namespace="annout")
        except Exception:
            logger.exception("Error while calculating ddln_id")
            raise ExportError("Cannot calculate ddln_id")
        root_dir.joinpath('ddln_id').write_text(ddln_id)
        shutil.copytree(str(root_dir), str(destination_dir))


def calculate_ddln_id(directory, namespace):
    process = subprocess.run(['/bin/bash', _ddln_id_script_path, namespace], stdout=subprocess.PIPE, cwd=str(directory))
    process.check_returncode()
    return process.stdout.decode('utf-8')


_ddln_id_script_path = str(Path(settings.BASE_DIR) / 'cvat/exp-devtools/datatools/create_ddln_id.sh')
