from pathlib import Path
from typing import Any

from .constants import SubroutineFlowKeys
from .dynamic_data_object import DynamicDataObject

__all__ = ["parse_step", "safe_save_yaml"]


def parse_step(step: DynamicDataObject) -> tuple[str, dict]:
    """
    Extracts method name and keyword arguments from a DynamicDataObject
    representing a subroutine flow step.

    Supports two formats:
    - Explicit: { "method": "foo", "params": { "x": 1 } }
    - Implicit: { "method": "foo", "x": 1 }

    Args:
        step (DynamicDataObject): A single step in the subroutine flow.

    Raises:
        ValueError: If the step does not contain a valid method key.

    Returns:
        tuple[str, dict[str, Any]]: A tuple containing the method name and its kwargs.
    """

    step_dict: dict[str, Any] = step.to_obj()

    method_name_key = SubroutineFlowKeys.METHOD
    if method_name_key not in step_dict:
        raise ValueError("Method name not found in step data.")
    method_name = step_dict[method_name_key]

    kwargs_dict = (
        step_dict[SubroutineFlowKeys.KWARGS]
        if SubroutineFlowKeys.KWARGS in step_dict
        else {k: v for k, v in step_dict.items() if k != method_name_key}
    )

    return method_name, kwargs_dict


def safe_save_yaml(data_obj, file_path: Path, encoding="utf-8") -> None:
    """
    Safely save data to a YAML file.

    Utilizes the DynamicDataObject.to_yaml() method while
    preserving the original structure when saving lists.

    Args:
        data_obj: Data to save (DynamicDataObject, list[DynamicDataObject], dict, etc.)
        file_path: File path to save to
        encoding: File encoding (default: utf-8)
    """
    import yaml

    file_path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(data_obj, DynamicDataObject):
        # Case DynamicDataObject
        data_obj.to_yaml(file_path, encoding=encoding)
    elif isinstance(data_obj, list):
        # Case list[Any]
        try:
            # Convert DynamicDataObject in list to dict
            data_to_save = [
                item.to_obj() if isinstance(item, DynamicDataObject) else item
                for item in data_obj
            ]

            with open(file_path, "w", encoding=encoding) as writer:
                yaml.safe_dump(data_to_save, writer, default_flow_style=False)
        except (IOError, OSError) as e:
            raise RuntimeError(f"Error writing to file {file_path}: {e}")
    else:
        # Case _
        converted = DynamicDataObject.from_obj(data_obj)
        if isinstance(converted, DynamicDataObject):
            converted.to_yaml(file_path, encoding=encoding)
        else:
            # Recursive call when from_obj returns a list
            safe_save_yaml(converted, file_path, encoding=encoding)
