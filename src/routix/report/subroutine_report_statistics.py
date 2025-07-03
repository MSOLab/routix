"""
subroutine_summary_statistics.py

SubroutineSummaryStatistics: Computes statistics and summary information from collected subroutine reports.
"""

from pathlib import Path
from typing import Any, Generic

from routix.utils import object_to_json, object_to_yaml

from .subroutine_report import SubroutineReportT
from .subroutine_report_recorder import SubroutineReportRecorder


class SubroutineReportStatistics(Generic[SubroutineReportT]):
    """Computes statistics and summary information from collected subroutine reports."""

    def __init__(self, recorder: SubroutineReportRecorder[SubroutineReportT]):
        self._recorder = recorder

    @property
    def name(self) -> str:
        return self._recorder.name

    @property
    def method_call_counts(self) -> dict[str, int]:
        return self._recorder.method_call_counts

    @property
    def reports(self) -> list[SubroutineReportT]:
        return self._recorder.reports

    @property
    def has_valid_objective_value(self) -> bool:
        return any(r.obj_value is not None for r in self.reports)

    @property
    def total_elapsed_time(self) -> float:
        return sum(r.elapsed_time for r in self.reports)

    @property
    def first_report(self) -> SubroutineReportT | None:
        return self.reports[0] if self.reports else None

    @property
    def last_report(self) -> SubroutineReportT | None:
        return self.reports[-1] if self.reports else None

    @property
    def valid_reports(self) -> list[SubroutineReportT]:
        return [r for r in self.reports if r.obj_value is not None]

    @property
    def min_obj_report(self) -> SubroutineReportT | None:
        fea = self.valid_reports
        if not fea:
            return None
        return min(
            fea,
            key=lambda r: r.obj_value if r.obj_value is not None else float("inf"),
        )

    @property
    def max_obj_report(self) -> SubroutineReportT | None:
        fea = self.valid_reports
        if not fea:
            return None
        return max(
            fea,
            key=lambda r: r.obj_value if r.obj_value is not None else float("-inf"),
        )

    def get_best_report(self, is_maximize: bool = False) -> SubroutineReportT | None:
        """Get the best report based on the objective value.

        Args:
            is_maximize (bool): True if the objective is to maximize, False if to minimize.

        Returns:
            SubroutineReportT | None: The best report based on objective value.
                - If is_maximize is True, returns the report with the maximum objective value.
                - If is_maximize is False, returns the report with the minimum objective value.
                - If no valid reports exist, returns None.
        """
        return self.max_obj_report if is_maximize else self.min_obj_report

    def get_improvement_ratio(self, is_maximize: bool = False) -> float | None:
        first = self.first_report
        best = self.get_best_report(is_maximize=is_maximize)
        if not (
            first
            and best
            and first.obj_value is not None
            and best.obj_value is not None
        ):
            return None
        if first.obj_value == 0:
            return None
        if is_maximize:
            return (best.obj_value - first.obj_value) / first.obj_value
        return (first.obj_value - best.obj_value) / first.obj_value

    # Serialization methods

    def to_dict(self, is_maximize: bool = False) -> dict[str, Any]:
        """Return a dictionary representation of the statistics.

        Args:
            is_maximize (bool, optional): True if the objective is to maximize, False if to minimize.
                Defaults to False.

        Returns:
            dict[str, Any]: A dictionary representation of the statistics.
        """
        first = self.first_report
        best = self.get_best_report(is_maximize=is_maximize)
        return {
            "instanceName": self.name,
            "foundFeasibleSol": self.has_valid_objective_value,
            "totalElapsedTime": self.total_elapsed_time,
            "firstObj": getattr(first, "obj_value", None) if first else None,
            "bestObj": getattr(best, "obj_value", None) if best else None,
            "bestBound": getattr(best, "obj_bound", None) if best else None,
            "improvementRatio": self.get_improvement_ratio(is_maximize),
            "methodCallCounts": f'"{self.method_call_counts}"',
            "reportCount": len(self.reports),
        }

    def to_yaml(self, file_path: Path, is_maximize: bool = False) -> None:
        object_to_yaml(self.to_dict(is_maximize), file_path)

    def to_json(self, file_path: Path, is_maximize: bool = False) -> None:
        object_to_json(self.to_dict(is_maximize), file_path)

    def to_string_dict(self, is_maximize: bool = False) -> dict[str, str]:
        """
        Return a dictionary with string representations of each field, suitable for CSV export.

        - Scalar fields are converted to strings.
        - Method call count dictionary is serialized with "".
          - If the log is empty, the string is empty.

        Args:
            is_maximize (bool, optional): True if the objective is to maximize, False if to minimize.
                Defaults to False.

        Returns:
            dict[str, str]: Dictionary with string representations.
        """
        data = self.to_dict(is_maximize=is_maximize)
        return_dict = {k: str(v) for k, v in data.items()}
        # Override dictionary
        return_dict["methodCallCounts"] = f'"{self.method_call_counts}"'

        return return_dict
