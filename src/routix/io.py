import json
from pathlib import Path
from typing import Any

import yaml

from .elapsed_timer import ElapsedTimer


def init_timestamped_working_dir(
    base_output_dir: Path, e_timer: ElapsedTimer | None = None
) -> Path:
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
    """Saves a Python object to a YAML file, ensuring Path objects are saved as strings.

    Args:
        obj (Any): The Python object to save.
            If it has a `to_dict` method, that will be used to convert it to a dictionary.
        path (Path): The file path where the YAML will be saved.
        encoding (str, optional): The encoding to use for the file. Defaults to "utf-8".
    """

    # Add a representer to handle pathlib.Path objects gracefully
    def path_representer(dumper: yaml.Dumper, data: Path) -> yaml.ScalarNode:
        return dumper.represent_scalar("!str", str(data))

    yaml.add_representer(Path, path_representer)

    # If the object has a to_dict method, use it to get a clean dictionary
    if hasattr(obj, "to_dict") and callable(getattr(obj, "to_dict")):
        data_to_dump = obj.to_dict()
    else:
        data_to_dump = obj

    with open(path, "w", encoding=encoding) as f:
        yaml.dump(data_to_dump, f, default_flow_style=False, sort_keys=False)

    # It's good practice to remove the representer if it's not needed globally
    yaml.Dumper.yaml_representers.pop(Path, None)


def object_to_json(obj: Any, path: Path, encoding: str = "utf-8") -> None:
    """Saves a Python object to a JSON file."""
    with open(path, "w", encoding=encoding) as f:
        json.dump(obj, f, indent=2)
