import inspect
import logging
from collections.abc import Mapping, Sequence
from typing import Any

from .constants import SubroutineFlowKeys
from .dynamic_data_object import DynamicDataObject


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

        def recursively_get(block: DynamicDataObject):
            if isinstance(block, Sequence) and not isinstance(block, (str, bytes)):
                for b in block:
                    recursively_get(b)
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
            method_name, kwargs_dict = SubroutineFlowKeys.parse_step(block.to_obj())
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

            # Check if unexpected arguments for the method are present
            sig = inspect.signature(getattr(self.controller_class, method_name))
            unexpected_args = [arg for arg in kwargs_dict if arg not in sig.parameters]
            if unexpected_args:
                errors.append(
                    {
                        "error": f"Unexpected arguments for '{method_name}': {unexpected_args}",
                        "block": block_obj,
                    }
                )
                return

        recursively_get(flow)
        return errors

    def explain(self, flow: DynamicDataObject) -> str:
        try:
            self.validate(flow)
            return "✅ Flow is valid."
        except ValueError as e:
            return f"❌ Flow is invalid:\n{str(e)}"

    def _fill_method_defaults(self, step: dict) -> dict:
        """Return a copy of step where missing optional keyword arguments are filled
        from the controller_class method signature defaults.

        The returned dict keeps the top-level method key and places kwargs as
        top-level keys (keeps SubroutineFlowKeys.KWARGS compatibility if used).
        """
        method_name, provided_kwargs = SubroutineFlowKeys.parse_step(step)

        if not hasattr(self.controller_class, method_name):
            raise ValueError(
                f"Method '{method_name}' not found on controller {self.controller_class}"
            )

        # Resolve the underlying function for staticmethod/classmethod
        attr = inspect.getattr_static(self.controller_class, method_name)
        if isinstance(attr, staticmethod) or isinstance(attr, classmethod):
            func = attr.__func__
        else:
            func = getattr(self.controller_class, method_name)

        sig = inspect.signature(func)

        merged = {k: v for k, v in provided_kwargs.items()}

        for param in sig.parameters.values():
            name = param.name
            if name in ("self", "cls"):
                continue
            if param.kind not in (
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                inspect.Parameter.KEYWORD_ONLY,
            ):
                continue
            if param.default is not inspect._empty and name not in merged:
                # don't deepcopy here; leave default as-is (immutable by convention)
                merged[name] = param.default

        # Build result preserving method top-level key and flattening kwargs
        result = {SubroutineFlowKeys.METHOD: method_name}
        result.update(merged)
        return result

    def normalize(self, obj) -> Any:
        """
        Normalize a subroutine-flow element into a JSON-compatible, canonical
        Python structure suitable for equality/subset comparison.

        Rules:
        - If the object has `to_obj()` or `to_dict()` use that representation.
        - dict: produce a new dict with normalized values and sorted keys.
        - list/tuple/Sequence: produce a list of normalized elements.
        - other objects: try to use __dict__ or vars(); fall back to the object itself.
        - primitives are returned as-is.

        This function intentionally returns plain Python types (dict, list, int,
        float, str, bool, None) so comparisons are predictable across runs.
        """

        logger = logging.getLogger(__name__)

        # track visited container/object ids to detect cycles (id-based)
        seen: set[int] = set()

        def recursively_normalize(x):
            # Convert known wrapper objects first
            try:
                if isinstance(x, DynamicDataObject):
                    try:
                        x = x.to_obj()
                    except Exception:
                        logger.exception("DynamicDataObject.to_obj() failed for %r", x)
                        raise
            except Exception:
                # If isinstance check itself fails for some reason, propagate
                raise

            if hasattr(x, "to_obj") and callable(getattr(x, "to_obj")):
                try:
                    x = x.to_obj()
                except Exception:
                    logger.exception("to_obj() failed for %r", x)
                    raise
            elif hasattr(x, "to_dict") and callable(getattr(x, "to_dict")):
                try:
                    x = x.to_dict()
                except Exception:
                    logger.exception("to_dict() failed for %r", x)
                    raise

            # Use structural pattern matching (Python 3.11+)
            match x:
                case Mapping():
                    obj_id = id(x)
                    if obj_id in seen:
                        return f"<cycle:{obj_id}>"
                    seen.add(obj_id)
                    try:
                        # Work on a concrete dict copy so we can mutate/inspect
                        mapping = dict(x)
                        # If this mapping is a subroutine step, fill missing optional kwargs
                        if SubroutineFlowKeys.METHOD in mapping:
                            try:
                                mapping = self._fill_method_defaults(mapping)
                            except Exception:
                                logger.exception(
                                    "Failed to fill method defaults for step: %r",
                                    mapping,
                                )
                                raise

                        normed = {}
                        # Coerce all dict keys to strings for JSON consistency
                        for k in sorted(mapping.keys(), key=lambda s: str(s)):
                            normed_k = str(k)
                            normed[normed_k] = recursively_normalize(mapping[k])
                        return normed
                    finally:
                        seen.remove(obj_id)

                case Sequence() if not isinstance(x, (str, bytes, bytearray)):
                    obj_id = id(x)
                    if obj_id in seen:
                        return f"<cycle:{obj_id}>"
                    seen.add(obj_id)
                    try:
                        return [recursively_normalize(e) for e in x]
                    finally:
                        seen.remove(obj_id)

                case _ if hasattr(x, "__dict__") and not isinstance(
                    x, (str, bytes, bytearray)
                ):
                    obj_id = id(x)
                    if obj_id in seen:
                        return f"<cycle:{obj_id}>"
                    seen.add(obj_id)
                    try:
                        try:
                            return recursively_normalize(vars(x))
                        except Exception:
                            logger.exception("vars() serialization failed for %r", x)
                            raise
                    finally:
                        seen.remove(obj_id)

                case _:
                    return x

        return recursively_normalize(obj)

    def validate_subroutine_flow_prefix(
        self,
        resume_flow: list[DynamicDataObject],
        current_flow: list[DynamicDataObject],
    ) -> int:
        """Strictly validate that `resume_flow` is a prefix of `current_flow`.

        Args:
            resume_flow (list[DynamicDataObject]): The flow to resume from.
            current_flow (list[DynamicDataObject]): The current flow of execution.

        Returns:
            int: the index in `current_flow` where execution should resume (i.e. len(resume_flow)).
                Raises ValueError on mismatch.
        """
        if not isinstance(resume_flow, list):
            raise TypeError("resume_flow must be a list of DynamicDataObject")
        if not isinstance(current_flow, list):
            raise TypeError("current_flow must be a list of DynamicDataObject")

        if len(resume_flow) > len(current_flow):
            raise ValueError(
                f"Resume flow length ({len(resume_flow)}) is greater than current flow length ({len(current_flow)})"
            )

        for i, r_elem in enumerate(resume_flow):
            c_elem = current_flow[i]
            r_norm = self.normalize(r_elem)
            c_norm = self.normalize(c_elem)
            if r_norm != c_norm:
                raise ValueError(
                    {
                        "error": "Subroutine flow prefix mismatch",
                        "index": i,
                        "resume_element": r_norm,
                        "current_element": c_norm,
                    }
                )

        return len(resume_flow)


def is_static_or_instance_method(cls: type, method_name: str) -> bool:
    """
    Checks whether the named attribute on the class is either a static method
    or an instance method, excluding classmethods and properties.

    Args:
        cls (type): The class to inspect.
        method_name (str): The name of the method to check.

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
    # Static method
    if isinstance(attr, staticmethod):
        return True
    # Exclude classmethod and property
    if isinstance(attr, classmethod) or isinstance(attr, property):
        return False
    # Regular instance function defined on the class
    if inspect.isfunction(attr):
        return True
    # Fall back: if the attribute on the class is callable, accept it
    val = getattr(cls, method_name, None)
    return callable(val)


def get_list_of_missing_required_arguments(
    cls: type, method_name: str, kwargs_dict: dict[str, DynamicDataObject]
) -> list[str]:
    """
    Get a list of arguments in the kwargs_dict are not in the method's signature.

    Args:
        cls (type): The class to inspect.
        method_name (str): The name of the method to check.
        kwargs_dict (dict[str, DynamicDataObject]): The dictionary of keyword arguments.

    Returns:
        list[str]: A list of missing required arguments.
    """
    method = getattr(cls, method_name)
    if not callable(method):
        raise TypeError(f"'{method_name}' is not a callable object")
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
