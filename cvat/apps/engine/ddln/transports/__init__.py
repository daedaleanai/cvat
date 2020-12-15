from .csv import CsvDirectoryExporter, CsvZipExporter, CsvDirectoryImporter, CsvZipImporter
from .cvat import CVATExporter, CVATImporter


def migrate(importer, exporter, handler):
    with exporter as exporter_rv:
        for frame_reader in importer.iterate_frames():
            frame_index = getattr(frame_reader, "index", None)
            handler.begin_frame(frame_reader.sequence_name, frame_reader.name, frame_index)
            with exporter_rv.begin_frame(frame_reader.name, frame_reader.sequence_name) as frame_writer:
                pass_image_dimensions(frame_reader, frame_writer)
                for object in handler.iterate_objects(frame_reader):
                    handler.write_object(object, frame_writer)


def pass_image_dimensions(reader, writer):
    if reader.image_width is None and writer.image_width is None:
        # Only CVAT Exporters/importers know image dimensions
        raise TypeError("Either exporter or importer should be CVAT instance")
    if reader.image_width is None:
        reader.image_width = writer.image_width
        reader.image_height = writer.image_height
    elif writer.image_width is None:
        writer.image_width = reader.image_width
        writer.image_height = reader.image_height
