import logging
import shutil
import stat
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from django.conf import settings

from cvat.apps.engine.models import Task
from .tasks import create_task_handler
from .transports import CVATImporter, CsvDirectoryExporter, migrate
from .utils import write_task_mapping_file, DdlnYamlWriter, guess_task_name

logger = logging.getLogger(__name__)

TARGET_DIR_PERMS = stat.S_ISGID | stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH
DDLN_ID_CALCULATION_SCRIPT_PATH = str(Path(settings.BASE_DIR) / 'cvat/exp-devtools/datatools/create_ddln_id.sh')


class ExportError(Exception):
    pass


def export_annotation(task_id, task_type, file_path):
    task = Task.objects.get(pk=task_id)
    if task.times_annotated == 1:
        export_single_annotation(task, task_type)
    else:
        export_mutiannotation(task, file_path)


def export_single_annotation(task, task_type):
    task_name = guess_task_name(task.name)
    destination_dir = settings.OUTGOING_TASKS_ROOT / task_name
    if destination_dir.exists():
        raise ExportError("Task has already been exported")

    with TemporaryDirectory() as root_dir_name:
        root_dir = Path(root_dir_name)
        task_mapping_file = root_dir / 'task_mapping.csv'
        ddln_yaml_file = root_dir / 'ddln.yaml'

        handler = create_task_handler(task_type)
        importer, _ = CVATImporter.for_task(task.id)
        exporter = CsvDirectoryExporter(root_dir, clear_if_exists=False)
        migrate(importer, exporter, handler)

        sequences = handler.load_sequences(importer)
        reporter = handler.validate(sequences)
        if reporter.has_violations(reporter.severity.ERROR):
            raise ExportError("Task has validation errors. Please run the validation.")

        write_task_mapping_file(task, task_mapping_file.open('w'))
        yaml_writer = DdlnYamlWriter(task.name)
        yaml_writer.write_metadata(ddln_yaml_file.open('wt'))
        warnings = yaml_writer.get_warnings()
        if warnings:
            message = ", ".join(warnings)
            raise ExportError(message)
        _finalize_export(root_dir, destination_dir)


def export_mutiannotation(task, file_path):
    root_dir = Path(file_path)
    task_name = guess_task_name(task.name)
    destination_dir = settings.OUTGOING_TASKS_ROOT / task_name
    if destination_dir.exists():
        raise ExportError("Task has already been exported")
    _finalize_export(root_dir, destination_dir)


def _finalize_export(root_dir, destination_dir):
    try:
        ddln_id = calculate_ddln_id(root_dir, namespace="annout")
    except Exception:
        logger.exception("Error while calculating ddln_id")
        raise ExportError("Cannot calculate ddln_id")
    root_dir.joinpath('ddln_id').write_text(ddln_id)
    root_dir.chmod(TARGET_DIR_PERMS)
    shutil.copytree(str(root_dir), str(destination_dir))


def calculate_ddln_id(directory, namespace):
    process = subprocess.run(
        ['/bin/bash', DDLN_ID_CALCULATION_SCRIPT_PATH, namespace],
        stdout=subprocess.PIPE,
        cwd=str(directory)
    )
    process.check_returncode()
    return process.stdout.decode('utf-8')
