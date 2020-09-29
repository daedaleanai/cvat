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
