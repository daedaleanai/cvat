from cvat.apps.engine.ddln.transports import CVATExporter
from .persistence.csv import HintsCsvImporter
from .persistence.cvat import HintWriter

def load_hints(hints_dir, task):
    exporter, task_annotation = CVATExporter.for_task(task.id)
    with exporter:
        for sequence_reader in HintsCsvImporter(hints_dir).iterate_sequences():
            hint_writer = HintWriter(exporter, sequence_reader.sequence_name)
            for frame_reader in sequence_reader.iterate_frames():
                for hint in frame_reader.iterate_hints():
                    hint_writer.write(hint, frame_reader.name, frame_reader.sequence_name)
            hint_writer.finish()
    task_annotation.create(exporter._annotations.data.serialize())
