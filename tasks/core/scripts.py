import sys
from pathlib import Path
from types import ModuleType


def import_module_from_path(module_name: str, module_path: str) -> ModuleType:
    import importlib.util

    absolute_path = Path(module_path).resolve()
    parent_path = absolute_path.parent

    sys.path.insert(0, str(parent_path))

    try:
        spec = importlib.util.spec_from_file_location(module_name, absolute_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            return module
        else:
            raise ImportError(f"Unable to load module: {module_name}")
    finally:
        sys.path.pop(0)
        exc_type, exc_value, _ = sys.exc_info()
        if exc_type is not None:
            raise exc_value


make = import_module_from_path(
    "make",
    "development/make.py",
)
make_build = import_module_from_path(
    "make_build",
    "development/make_build.py",
)
