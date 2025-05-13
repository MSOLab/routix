import inspect
from collections.abc import Sequence

from .constants import SubroutineFlowKeys
from .dynamic_data_object import DynamicDataObject
from .utils import parse_step


class SubroutineFlowValidator:
    def __init__(self, controller_class: type):
        self.controller_class = controller_class

    def validate(self, flow: DynamicDataObject) -> bool:
        errors = self.get_invalid_blocks(flow)
        if errors:
            raise ValueError(f"Invalid subroutine flow: {errors}")
        return True

    def get_invalid_blocks(self, flow: DynamicDataObject) -> list[dict]:
        errors: list[dict] = []

        def recurse(block: DynamicDataObject):
            if isinstance(block, Sequence) and not isinstance(block, (str, bytes)):
                for b in block:
                    recurse(b)
                return

            # The block is not a sequence, so we check if it's a dict
            block_obj = block.to_obj() if hasattr(block, "to_obj") else block
            if not isinstance(block_obj, dict):
                errors.append({"error": "Not a dict", "block": block})
                return

            # Check if the block has a method key
            method_key = SubroutineFlowKeys.METHOD
            if method_key not in block_obj:
                errors.append({"error": f"Missing {method_key}", "block": block_obj})
                return

            # Check if the method name is a string
            method_name, kwargs_dict = parse_step(block)
            if not isinstance(method_name, str):
                errors.append({"error": f"Non-string {method_key}", "block": block_obj})
                return

            # Check if the method exists in the controller class
            if not hasattr(self.controller_class, method_name):
                errors.append(
                    {"error": f"Method '{method_name}' not found", "block": block_obj}
                )
                return

            # Check if the method is callable
            if not is_static_or_instance_method(self.controller_class, method_name):
                errors.append(
                    {
                        "error": f"Method '{method_name}' is not callable",
                        "block": block_obj,
                    }
                )
                return

            # Check if the kwargs_dict is a dict
            kwargs_key = SubroutineFlowKeys.KWARGS
            if not isinstance(kwargs_dict, dict):
                errors.append(
                    {
                        "error": f"Non-dict {kwargs_key}",
                        "block": block_obj,
                    }
                )
                return

            # Check if required arguments for the method are present
            missing_args = get_list_of_missing_required_arguments(
                self.controller_class, method_name, kwargs_dict
            )
            if missing_args:
                errors.append(
                    {
                        "error": f"Missing required arguments for '{method_name}': {missing_args}",
                        "block": block_obj,
                    }
                )
                return

        recurse(flow)
        return errors

    def explain(self, flow: DynamicDataObject) -> str:
        try:
            self.validate(flow)
            return "✅ Flow is valid."
        except ValueError as e:
            return f"❌ Flow is invalid:\n{str(e)}"


def is_static_or_instance_method(cls: type, method_name: str) -> bool:
    """
    Checks whether the named attribute on the class is either a static method
    or an instance method, excluding classmethods and properties.

    Args:
        cls (type): The class to inspect.
        name (str): The name of the method to check.

    Returns:
        bool: True if the attribute is a valid static or instance method.
              False otherwise.

    Valid:
        - def method(self): ...
        - @staticmethod

    Invalid:
        - @classmethod
        - @property
        - Plain data attributes
    """
    if not hasattr(cls, method_name):
        return False

    attr = inspect.getattr_static(cls, method_name)

    # Check if the attribute is callable (e.g., a callable object)
    if callable(getattr(cls, method_name)):
        if isinstance(attr, staticmethod):
            return True
        if inspect.isfunction(attr):
            return True  # Regular instance method

    return False


def get_list_of_missing_required_arguments(
    cls: type, method_name: str, kwargs_dict: dict[str, DynamicDataObject]
) -> list[str]:
    """
    Check if all arguments in the kwargs_dict are present in the method's signature.

    Args:
        method (callable): The method to check.
        kwargs_dict (dict[str, DynamicDataObject]): The dictionary of keyword arguments.

    Returns:
        bool: True if all arguments are present, False otherwise.
    """
    method = getattr(cls, method_name)

    sig = inspect.signature(method)
    required_args = [
        param.name
        for param in sig.parameters.values()
        if param.default is param.empty
        and param.kind
        in (
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        )
        and param.name not in ("self", "cls")
    ]
    return [arg for arg in required_args if arg not in kwargs_dict.keys()]
