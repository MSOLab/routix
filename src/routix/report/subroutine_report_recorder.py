from typing import Generic

from .subroutine_report import SubroutineReportT


class SubroutineReportRecorder(Generic[SubroutineReportT]):
    """Collects method call counts and subroutine reports during experiment execution."""

    def __init__(self, name: str) -> None:
        self.name: str = name
        self.method_call_counts: dict[str, int] = {}
        self.reports: list[SubroutineReportT] = []

    def increment_method_call_count(self, method_name: str) -> None:
        self.method_call_counts[method_name] = (
            self.method_call_counts.get(method_name, 0) + 1
        )

    def append_report(self, subroutine_report: SubroutineReportT) -> None:
        self.reports.append(subroutine_report)
