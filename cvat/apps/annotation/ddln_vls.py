# Copyright (C) 2020

format_spec = {
    "name": "DDLN_CSV_VLS",
    "dumpers": [
        {
            "display_name": "{name} {format} {version}",
            "format": "ZIP",
            "version": "0.2",
            "handler": "dump"
        }
    ],
}


def dump(file_object, annotations):
    import io
    from cvat.apps.annotation.transports.csv import CsvZipExporter
    from cvat.apps.annotation.transports.cvat import CVATImporter
    from cvat.apps.annotation.transports.cvat.utils import FileLogger

    buffer = io.StringIO()
    logger = FileLogger(buffer)
    importer = CVATImporter(annotations, logger)
    with CsvZipExporter(file_object) as exporter:
        for frame_reader in importer.iterate_frames():
            with exporter.begin_frame(frame_reader.name, frame_reader.sequence_name) as frame_writer:
                for runway in frame_reader.iterate_runways():
                    frame_writer.write_runway(runway)
        zip_archive = exporter.get_archive()
        zip_archive.writestr('validation.log', buffer.getvalue())
