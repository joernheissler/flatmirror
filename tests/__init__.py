import importlib.util
import sys
from importlib.machinery import SourceFileLoader
from types import ModuleType


def import_from_file(module_name: str, file_path: str) -> ModuleType:
    loader = SourceFileLoader(module_name, file_path)
    spec = importlib.util.spec_from_file_location(module_name, loader=loader)
    assert spec
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    loader.exec_module(module)
    return module


flatmirror = import_from_file("flatmirror", "flatmirror")
