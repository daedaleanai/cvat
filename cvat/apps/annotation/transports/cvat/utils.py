import itertools

from cvat.apps.engine.utils import natural_order


def build_attrs_dict(shape):
    return {a.name: a.value for a in shape.attributes}


class FileLogger:
    def __init__(self, log_file):
        self._log_file = log_file
        self.prefix = None

    def log(self, message):
        if self.prefix:
            message = "{}{}".format(self.prefix, message)
        self._log_file.write(message)
        self._log_file.write('\n')


def write_task_mapping_file(task, file):
    assignment_data = task.get_assignment_data()
    assignment_data.sort(key=lambda row: (row[0], natural_order(row[1])))
    for version, group in itertools.groupby(assignment_data, key=lambda row: row[0]):
        file.write("V{}:\n".format(version + 1))
        for _, sequence_name, annotator_name in group:
            file.write("{}\t{}\n".format(sequence_name, annotator_name or ''))
        file.write("\n")
