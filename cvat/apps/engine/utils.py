import ast
import itertools
import re
from collections import namedtuple
import importlib
import sys
import traceback

Import = namedtuple("Import", ["module", "name", "alias"])

def parse_imports(source_code: str):
    root = ast.parse(source_code)

    for node in ast.iter_child_nodes(root):
        if isinstance(node, ast.Import):
            module = []
        elif isinstance(node, ast.ImportFrom):
            module = node.module
        else:
            continue

        for n in node.names:
            yield Import(module, n.name, n.asname)

def import_modules(source_code: str):
    results = {}
    imports = parse_imports(source_code)
    for import_ in imports:
        module = import_.module if import_.module else import_.name
        loaded_module = importlib.import_module(module)

        if not import_.name == module:
            loaded_module = getattr(loaded_module, import_.name)

        if import_.alias:
            results[import_.alias] = loaded_module
        else:
            results[import_.name] = loaded_module

    return results

class InterpreterError(Exception):
    pass

def execute_python_code(source_code, global_vars=None, local_vars=None):
    try:
        exec(source_code, global_vars, local_vars)
    except SyntaxError as err:
        error_class = err.__class__.__name__
        details = err.args[0]
        line_number = err.lineno
        raise InterpreterError("{} at line {}: {}".format(error_class, line_number, details))
    except AssertionError as err:
        # AssertionError doesn't contain any args and line number
        error_class = err.__class__.__name__
        raise InterpreterError("{}".format(error_class))
    except Exception as err:
        error_class = err.__class__.__name__
        details = err.args[0]
        _, _, tb = sys.exc_info()
        line_number = traceback.extract_tb(tb)[-1][1]
        raise InterpreterError("{} at line {}: {}".format(error_class, line_number, details))


def load_instances(model, primary_keys):
    """Load model instances preserving order of keys in the list."""
    instance_by_pk = model.objects.in_bulk(primary_keys)
    return [instance_by_pk[pk] for pk in primary_keys]


def group_on_delimiter(iterable, delimiter):
    """Group elements separated by delimiter into chunks.

    group(['a', 'b', '', 'c', 'd', '', 'e'], '') => [['a', 'b'], ['c', 'd'], ['e']]
    """
    return [list(g) for is_delimiter, g in itertools.groupby(iterable, lambda el: el == delimiter) if not is_delimiter]


def natural_order(text):
    """Key function for sorting in 'human' order.
    That way string "TP14_a2a2_13_1" goes after "TP14_a2a2_2_0", not before.
    """
    return [_try_int(c) for c in re.split(r'(\d+)', text)]


def _try_int(text):
    return int(text) if text.isdigit() else text
