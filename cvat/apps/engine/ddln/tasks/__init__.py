from .spotter import SpotterTaskHandler
from .vls import VlsTaskHandler


def create_task_handler(task_type):
    if task_type == "spotter":
        return SpotterTaskHandler()
    if task_type == "vls":
        return VlsTaskHandler()
    raise ValueError("Unexpected task type: {!r}".format(task_type))
