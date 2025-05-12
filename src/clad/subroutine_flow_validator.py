import inspect
from collections.abc import Sequence

from .dynamic_data_object import DynamicDataObject


class SubroutineFlowValidator:
    def __init__(self, controller_class: type):
        self.controller_class = controller_class

    def validate(self, flow: DynamicDataObject) -> bool:
        self.get_invalid_blocks(flow)  # raises if any
        return True

    def get_invalid_blocks(self, flow: DynamicDataObject) -> list[dict]:
        errors = []

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

            # Check if the block has a "method_name" key
            if "method_name" not in block_obj:
                errors.append({"error": "Missing method_name", "block": block_obj})
                return

            # Check if the method_name is a string
            method = block_obj["method_name"]
            if not isinstance(method, str):
                errors.append({"error": "Non-string method_name", "block": block_obj})
                return

            # Check if the method exists in the controller class
            if not hasattr(self.controller_class, method):
                errors.append(
                    {"error": f"Method '{method}' not found", "block": block_obj}
                )
                return

            # Check if the method is callable
            if not is_static_or_instance_method(self.controller_class, method):
                errors.append(
                    {"error": f"Method '{method}' is not callable", "block": block_obj}
                )

        recurse(flow)
        if errors:
            raise ValueError(f"Invalid subroutine flow: {errors}")
        return []

    def explain(self, flow: DynamicDataObject) -> str:
        try:
            self.get_invalid_blocks(flow)
            return "✅ Flow is valid."
        except ValueError as e:
            return f"❌ Flow is invalid:\n{str(e)}"


def is_static_or_instance_method(cls: type, name: str) -> bool:
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
    if not hasattr(cls, name):
        return False

    attr = inspect.getattr_static(cls, name)

    if isinstance(attr, staticmethod):
        return True

    if inspect.isfunction(attr):
        return True  # Regular instance method

    return False
