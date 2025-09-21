import json
import re
from pathlib import Path, PurePath
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


def yaml_to_object(path: PurePath, encoding: str = "utf-8") -> Any:
    """Loads a Python object from a YAML file.

    Args:
        path (PurePath): The file path from which to load the YAML.
        encoding (str, optional): The encoding to use for the file. Defaults to "utf-8".

    Returns:
        Any: The Python object loaded from the YAML file.
    """
    with open(path, "r", encoding=encoding) as f:
        return yaml.safe_load(f)


def tuple_to_pyyaml_key(d: dict) -> dict:
    """
    tuple 형태의 key를 '!!python/tuple [j0,i0,i0_1]' 형태로 변환

    reference: solution_manager.py row 66
    """
    new_dict = {}
    for k, v in d.items():
        if isinstance(k, tuple):
            # 내부 요소를 쉼표로 연결하고 strip
            items = ", ".join(str(item).strip() for item in k)
            new_dict[f"!!python/tuple [{items}]"] = v
        else:
            new_dict[k] = v
    return new_dict


def pyyaml_key_to_tuple(d: dict) -> dict:
    """
    '!!python/tuple [j0,i0,i0_1]' 형태의 key를 tuple로 변환

    reference: solution_manager.py row 66
    """
    tuple_key_pattern = re.compile(r"^!!python/tuple \[(.*)\]$")
    new_dict = {}
    for k, v in d.items():
        m = tuple_key_pattern.match(k)
        if m:
            # 내부 요소를 쉼표로 분리하고 strip
            items = [item.strip() for item in m.group(1).split(",")]
            new_dict[tuple(items)] = v
        else:
            new_dict[k] = v
    return new_dict


def extract_prefix_from_filename(pattern: str, filename: str) -> str | None:
    """Extracts the prefix from a filename based on a given pattern.

    For example, pattern `{}_obj_log.yaml` will match filename `0_obj_log.yaml` and extract "0".

    Args:
        pattern (str): Pattern to match the filename, with {} for the prefix.
        filename (str): Filename to extract the prefix from.

    Returns:
        str | None: The extracted prefix or None if not matched.
    """
    # Escape special regex chars except {}
    regex = re.escape(pattern).replace(r"\{\}", "(.+?)")
    match = re.match(regex, filename)
    if match:
        return match.group(1)
    return None
