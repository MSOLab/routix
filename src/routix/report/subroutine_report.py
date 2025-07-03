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

    def to_dict(self) -> dict[str, Any]:
        """Return a dictionary representation of this report, suitable for serialization."""
        return asdict(self)

    def to_string_dict(self) -> dict[str, str]:
        """Return a dictionary with string representations of each field, suitable for CSV export.


        Returns:
            dict[str, str]: Dictionary with string representations of:
                - "elapsed_time"
                - "obj_value"
                - "obj_bound"
        """
        return {
            "elapsed_time": str(self.elapsed_time),
            "obj_value": str(self.obj_value) if self.obj_value is not None else "",
            "obj_bound": str(self.obj_bound) if self.obj_bound is not None else "",
        }

    def __str__(self) -> str:
        return (
            f"SubroutineReport(elapsed_time={self.elapsed_time!s}, "
            f"obj_value={self.obj_value!s}, obj_bound={self.obj_bound!s}, "
        )

    def __repr__(self) -> str:
        return (
            f"SubroutineReport(elapsed_time={self.elapsed_time!r}, "
            f"obj_value={self.obj_value!r}, obj_bound={self.obj_bound!r}, "
        )


SubroutineReportT = TypeVar("SubroutineReportT", bound=SubroutineReport)
"""
Type variable for SubroutineReport, allowing methods to specify
that they return or accept an instance of SubroutineReport or its subclasses.
"""
