from typing import Any

from .constants import SubroutineFlowKeys
from .dynamic_data_object import DynamicDataObject


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
