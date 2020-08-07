from pathlib import PurePath


def parse_frame_name(path):
    image_path = PurePath(path)
    sequence_name = image_path.parents[2].name
    frame_name = image_path.stem
    return frame_name, sequence_name


def build_attrs_dict(shape):
    return {a.name: a.value for a in shape.attributes}


def grouper(iterable, n):
    """Collect data into fixed-length chunks or blocks"""
    # grouper('ABCDEF', 3) --> ABC DEF
    args = [iter(iterable)] * n
    return zip(*args)


class FileLogger:
    def __init__(self, log_file):
        self._log_file = log_file
        self.prefix = None

    def log(self, message):
        if self.prefix:
            message = "{}{}".format(self.prefix, message)
        self._log_file.write(message)
        self._log_file.write('\n')