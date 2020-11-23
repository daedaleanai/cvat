from .spotter import SpotterTaskHandler
from .vls import VlsTaskHandler


def create_task_handler(task_type):
    if task_type == "spotter":
        return SpotterTaskHandler()
    if task_type == "vls":
        return VlsTaskHandler()
    raise ValueError("Unexpected task type: {!r}".format(task_type))


def guess_task_type(task):
    labels_names = {label.name for label in task.label_set.all()}
    is_spotter_task = 'Helicopter' in labels_names and 'Fixed wing aircraft' in labels_names
    is_vls_task = 'Runway' in labels_names
    if is_spotter_task == is_vls_task:
        return None
    if is_spotter_task:
        return "spotter"
    if is_vls_task:
        return "vls"
    return None
