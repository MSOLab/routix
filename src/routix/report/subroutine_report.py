from dataclasses import dataclass
from typing import Any, TypeVar


@dataclass(frozen=True)
class SubroutineReport:
    """
    Immutable report of a subroutine execution.

    This class captures the key results of a subroutine run, including:
    - Elapsed time in seconds
    - Final objective value (if available)
    - Final objective bound (if available)
    - Progress log: a list of (elapsed_time, objective_value, objective_bound) tuples

    All fields are read-only after creation.
    """

    elapsed_time: float
    """Total elapsed time for the subroutine execution, in seconds."""

    obj_value: float | None
    """Final objective value, or None if not available."""

    obj_bound: float | None
    """Final objective bound, or None if not available."""

    obj_progress_log: list[tuple[float, float, float]]
    """
    Progress log as a list of tuples:
        (elapsed_time, objective_value, objective_bound)
    Each entry records the state of the solver at a given time.
    """

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the report to a serializable dictionary.

        Returns:
            dict: Dictionary with keys 'elapsed_time', 'obj_value', 'obj_bound', and 'obj_progress_log'.
        """
        return {
            "elapsed_time": self.elapsed_time,
            "obj_value": self.obj_value,
            "obj_bound": self.obj_bound,
            "obj_progress_log": self.obj_progress_log,
        }


SubroutineReportT = TypeVar("SubroutineReportT", bound=SubroutineReport)
"""
Type variable for SubroutineReport, allowing methods to specify
that they return or accept an instance of SubroutineReport or its subclasses.
"""
