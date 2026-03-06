import json
import warnings
from pathlib import Path, PurePath
from typing import Any


def dump_json(obj: Any, path: PurePath, encoding: str = "utf-8") -> None:
    """Saves a Python object to a JSON file."""
    with open(path, "w", encoding=encoding) as f:
        json.dump(obj, f, indent=2)


def object_to_json(obj: Any, path: Path, encoding: str = "utf-8") -> None:
    warnings.warn(
        "object_to_json is deprecated, use dump_json instead",
        DeprecationWarning,
        stacklevel=2,
    )
    dump_json(obj, path, encoding=encoding)
