from .csv import CsvDirectoryExporter, CsvZipExporter, CsvDirectoryImporter, CsvZipImporter
from .cvat import CVATExporter, CVATImporter


def migrate(importer, exporter, handler):
    with exporter as exporter_rv:
        for frame_reader in importer.iterate_frames():
            frame_index = getattr(frame_reader, "index", None)
            handler.begin_frame(frame_reader.sequence_name, frame_reader.name, frame_index)
            with exporter_rv.begin_frame(frame_reader.name, frame_reader.sequence_name) as frame_writer:
                for object in handler.iterate_objects(frame_reader):
                    handler.write_object(object, frame_writer)
