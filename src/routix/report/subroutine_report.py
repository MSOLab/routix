from dataclasses import asdict, dataclass
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
        """Return a dictionary representation of this report, suitable for serialization.

        Returns:
            dict[str, Any]: Dictionary with the following keys:
                - 'elapsed_time' (float)
                - 'obj_value' (float or None)
                - 'obj_bound' (float or None)
                - 'obj_progress_log' (list of (float, float, float))
        """
        return asdict(self)

    def to_string_dict(self) -> dict[str, str]:
        """
        Return a dictionary with string representations of each field, suitable for CSV export.

        Scalar fields are converted to strings. The progress log is serialized as a semicolon-separated
        list of pipe-separated triples (e.g., "0.0|1.0|2.0;1.0|2.0|3.0"). If the log is empty,
        the string is empty.

        Returns:
            dict[str, str]: Dictionary with string representations of:
                - "elapsed_time"
                - "obj_value"
                - "obj_bound"
                - "obj_progress_log"
        """
        progress_log_str = ";".join(
            f"{t[0]}|{t[1]}|{t[2]}" for t in self.obj_progress_log
        )
        return {
            "elapsed_time": str(self.elapsed_time),
            "obj_value": str(self.obj_value) if self.obj_value is not None else "",
            "obj_bound": str(self.obj_bound) if self.obj_bound is not None else "",
            "obj_progress_log": progress_log_str,
        }

    def __str__(self) -> str:
        return (
            f"SubroutineReport(elapsed_time={self.elapsed_time!s}, "
            f"obj_value={self.obj_value!s}, obj_bound={self.obj_bound!s}, "
            f"obj_progress_log=[...{len(self.obj_progress_log)} entries...])"
        )

    def __repr__(self) -> str:
        return (
            f"SubroutineReport(elapsed_time={self.elapsed_time!r}, "
            f"obj_value={self.obj_value!r}, obj_bound={self.obj_bound!r}, "
            f"obj_progress_log=[...{len(self.obj_progress_log)} entries...])"
        )


SubroutineReportT = TypeVar("SubroutineReportT", bound=SubroutineReport)
"""
Type variable for SubroutineReport, allowing methods to specify
that they return or accept an instance of SubroutineReport or its subclasses.
"""
