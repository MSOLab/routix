import json
from pathlib import Path
from typing import Any


def object_to_json(obj: Any, path: Path, encoding: str = "utf-8") -> None:
    """Saves a Python object to a JSON file."""
    with open(path, "w", encoding=encoding) as f:
        json.dump(obj, f, indent=2)
