from .spotter import SpotterTaskHandler
from .vls import VlsTaskHandler
from .vls_lines import VlsLinesTaskHandler


def create_task_handler(task_type):
    if task_type == "spotter":
        return SpotterTaskHandler()
    if task_type == "vls":
        return VlsTaskHandler()
    if task_type == "vls-lines":
        return VlsLinesTaskHandler()
    raise ValueError("Unexpected task type: {!r}".format(task_type))


def guess_task_type(task):
    labels_names = {label.name for label in task.label_set.all()}
    is_spotter_task = 'Helicopter' in labels_names and 'Fixed wing aircraft' in labels_names
    is_vls_task = 'Runway' in labels_names
    is_vls_lines_task = 'Vertical line' in labels_names and 'Horizontal line' in labels_names
    is_type_uncertain = sum(v for v in [is_spotter_task, is_vls_task, is_vls_lines_task]) > 1
    if is_type_uncertain:
        return None
    if is_spotter_task:
        return "spotter"
    if is_vls_task:
        return "vls"
    if is_vls_lines_task:
        return "vls-lines"
    return None
