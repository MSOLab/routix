from pathlib import Path
from typing import Any
import yaml
import json

from .elapsed_timer import ElapsedTimer

def init_timestamped_working_dir(base_output_dir: Path, e_timer: ElapsedTimer | None = None) -> Path:
    """
    Creates and returns a timestamped working directory.

    If an ElapsedTimer instance is provided, it uses its start time.
    Otherwise, it creates a new ElapsedTimer instance.

    Args:
        base_output_dir (Path): The base directory where the new timestamped directory will be created.
        e_timer (ElapsedTimer | None, optional): An optional existing timer. Defaults to None.

    Returns:
        Path: The path to the created timestamped working directory.
    """
    if e_timer is None:
        e_timer = ElapsedTimer()
    
    working_dir = base_output_dir / e_timer.get_start_dt_for_dir_name()
    working_dir.mkdir(parents=True, exist_ok=True)
    return working_dir

def object_to_yaml(obj: Any, path: Path, encoding: str = "utf-8") -> None:
    """Saves a Python object to a YAML file."""
    with open(path, "w", encoding=encoding) as f:
        yaml.dump(obj, f, default_flow_style=False)

def object_to_json(obj: Any, path: Path, encoding: str = "utf-8") -> None:
    """Saves a Python object to a JSON file."""
    with open(path, "w", encoding=encoding) as f:
        json.dump(obj, f, indent=2)
