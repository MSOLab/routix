"""
subroutine_summary_statistics.py

SubroutineSummaryStatistics: Computes statistics and summary information from collected subroutine reports.
"""

from typing import Generic

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

    def found_feasible(self) -> bool:
        return any(r.obj_value is not None for r in self.reports)

    def get_first(self) -> SubroutineReportT | None:
        return self.reports[0] if self.reports else None

    def get_last(self) -> SubroutineReportT | None:
        return self.reports[-1] if self.reports else None

    def _valid_runs(self) -> list[SubroutineReportT]:
        return [r for r in self.reports if r.obj_value is not None]

    def get_minimum(self) -> SubroutineReportT | None:
        fea = self._valid_runs()
        if not fea:
            return None
        return min(
            fea,
            key=lambda r: r.obj_value if r.obj_value is not None else float("inf"),
        )

    def get_maximum(self) -> SubroutineReportT | None:
        fea = self._valid_runs()
        if not fea:
            return None
        return max(
            fea,
            key=lambda r: r.obj_value if r.obj_value is not None else float("-inf"),
        )

    def total_elapsed(self) -> float:
        return sum(r.elapsed_time for r in self.reports)

    def improvement_ratio(self, is_maximize: bool = False) -> float | None:
        first = self.get_first()
        best = self.get_maximum() if is_maximize else self.get_minimum()
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
