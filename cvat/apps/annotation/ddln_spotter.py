# Copyright (C) 2020

format_spec = {
    "name": "DDLN_CSV_BB",
    "dumpers": [
        {
            "display_name": "{name} {format} {version} for images [BB]",
            "format": "ZIP",
            "version": "0.9",
            "handler": "dump"
        }
    ],
    "loaders": [
        {
            "display_name": "{name} {format} {version} for images [BB]",
            "format": "ZIP",
            "version": "0.9",
            "handler": "load",
        }
    ],
}


def dump(file_object, annotations):
    from tempfile import TemporaryDirectory
    from cvat.apps.dataset_manager.util import make_zip_archive
    from cvat.apps.engine.ddln.transports import migrate, CsvDirectoryImporter, CsvDirectoryExporter, CVATImporter
    from cvat.apps.engine.ddln.tasks.spotter import SpotterTaskHandler
    from cvat.apps.engine.ddln.utils import write_task_mapping_file, DdlnYamlWriter

    with TemporaryDirectory() as temp_dir:
        importer = CVATImporter(annotations)
        exporter = CsvDirectoryExporter(temp_dir)
        handler = SpotterTaskHandler()
        migrate(importer, exporter, handler)

        sequences = handler.load_sequences(CsvDirectoryImporter(temp_dir))
        reporter = handler.validate(sequences)
        validation_file = os.path.join(temp_dir, 'validation.txt')
        reporter.write_text_report(open(validation_file, 'wt'), reporter.severity.WARNING)

        yaml_writer = DdlnYamlWriter(annotations.meta['task']['name'], add_merger_info=False)
        yaml_writer.write_metadata(open(os.path.join(temp_dir, "ddln.yaml"), 'w'))
        task_mapping_filename = os.path.join(temp_dir, 'task_mapping.csv')
        write_task_mapping_file(annotations._db_task, open(task_mapping_filename, 'wt'))
        make_zip_archive(temp_dir, file_object)


def load(file_object, annotations):
    from cvat.apps.engine.ddln.transports import migrate, CsvZipImporter, CVATExporter
    from cvat.apps.engine.ddln.tasks.spotter import SpotterTaskHandler

    importer = CsvZipImporter(file_object)
    exporter = CVATExporter(annotations)
    handler = SpotterTaskHandler()
    migrate(importer, exporter, handler)
