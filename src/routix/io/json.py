import json
from pathlib import PurePath
from typing import Any


def _json_default(obj: Any) -> Any:
    """Fallback serializer for non-JSON-native objects.

    - pathlib.PurePath (and subclasses) are converted to str.
    - Objects with a callable ``to_dict`` method are converted via that method.
    """
    if isinstance(obj, PurePath):
        return str(obj)

    to_dict = getattr(obj, "to_dict", None)
    if callable(to_dict):
        return to_dict()

    raise TypeError(f"Object of type {type(obj).__name__!r} is not JSON serializable")


def dump_json(obj: Any, path: PurePath, encoding: str = "utf-8") -> None:
    """Saves a Python object to a JSON file."""
    with open(path, "w", encoding=encoding) as f:
        json.dump(obj, f, indent=2, default=_json_default)
