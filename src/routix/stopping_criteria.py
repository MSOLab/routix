from typing import Any, TypeVar

from .dynamic_data_object import DynamicDataObject


class StoppingCriteria(DynamicDataObject):
    """
    Basic stopping criteria for subroutine controller.

    This class encapsulates the parameters that determine when an algorithm should terminate.
    Typical criteria include time limits, iteration limits, or convergence thresholds.
    The default implementation provides a time limit,
    but this class can be extended to support additional or custom stopping conditions.

    Attributes:
        timelimit (float): Maximum time allowed for the algorithm to run, in seconds.
    """

    timelimit: float
    """Maximum time allowed for the algorithm to run, in seconds."""

    def __init__(self, param_dict: dict[str, Any]):
        super().__init__(param_dict)


StoppingCriteriaT = TypeVar("StoppingCriteriaT", bound=StoppingCriteria)
"""
Type variable for StoppingCriteria, allowing methods to specify
that they return or accept an instance of StoppingCriteria or its subclasses.
"""
