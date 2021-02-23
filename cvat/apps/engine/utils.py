import ast
import itertools
import json
import re
import threading
import os.path
from collections import namedtuple
import importlib
import sys
import traceback
from functools import wraps
from pathlib import Path

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


def cached(key_prefix, timeout=None, cache_name="default"):
    from django.core.cache import caches
    cache = caches[cache_name]

    def inner(func):
        def wrapper(*args, **kwargs):
            key = json.dumps(dict(a=args, k=kwargs))
            key = key_prefix + key
            rv = cache.get(key)
            if rv is None:
                rv = func(*args, **kwargs)
                cache.set(key, rv, timeout)
            return rv
        return wrapper
    return inner


def safe_path_join(base_dir, path):
    base_dir = Path(base_dir)
    path = Path(path)
    path = path.relative_to('/') if path.is_absolute() else path
    path = base_dir / path
    path = Path(os.path.normpath(str(path)))
    try:
        path.relative_to(base_dir)
    except ValueError:
        raise ValueError("Path {} is outside of {} dir".format(path, base_dir)) from None
    return path


def singleton(constructor):
    """Decorator for turning function into singleton constructor. Function should take no arguments."""
    storage = threading.local()

    @wraps(constructor)
    def inner():
        if getattr(storage, "instance", None) is None:
            storage.instance = constructor()
        return storage.instance

    return inner


def load_instances(model, primary_keys):
    """Load model instances preserving order of keys in the list."""
    instance_by_pk = model.objects.in_bulk(primary_keys)
    return [instance_by_pk[pk] for pk in primary_keys]


def find_range(iterable, predicate):
    """Find the indices of the first range of consecutive items which satisfy the given predicate.
    Returns (-1, -1) if it there is no such ranges.

    find_range([0, 0, 1, 1, 0], lambda e: e > 0) => (2, 4)
    """
    iterator = enumerate(iterable)
    start_index = next((i for i, value in iterator if predicate(value)), -1)
    if start_index == -1:
        return -1, -1
    j = start_index
    for j, value in iterator:
        if not predicate(value):
            end_index = j
            break
    else:
        end_index = j + 1
    return start_index, end_index


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


def grouper(iterable, n):
    """Collect data into fixed-length chunks or blocks"""
    # grouper('ABCDEF', 3) --> ABC DEF
    args = [iter(iterable)] * n
    return zip(*args)
