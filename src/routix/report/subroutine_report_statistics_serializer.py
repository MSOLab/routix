"""
subroutine_summary_serializer.py

SubroutineSummarySerializer: Serializes summary statistics to dict, JSON, or YAML.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Generic

from ..utils import object_to_json, object_to_yaml
from .subroutine_report import SubroutineReportT
from .subroutine_report_statistics import SubroutineReportStatistics


@dataclass
class SubroutineReportStatisticsSerializer(Generic[SubroutineReportT]):
    """Serializes report statistics to dict, JSON, or YAML."""

    stats: SubroutineReportStatistics[SubroutineReportT]

    def to_dict(self, is_maximize: bool = False) -> Dict[str, Any]:
        first = self.stats.get_first()
        best = self.stats.get_maximum() if is_maximize else self.stats.get_minimum()
        return {
            "instanceName": self.stats.name,
            "foundFeasibleSol": self.stats.found_feasible(),
            "totalElapsedTime": self.stats.total_elapsed(),
            "firstObj": getattr(first, "obj_value", None) if first else None,
            "bestObj": getattr(best, "obj_value", None) if best else None,
            "bestBound": getattr(best, "obj_bound", None) if best else None,
            "improvementRatio": self.stats.improvement_ratio(is_maximize),
            "methodCallCounts": f'"{self.stats.method_call_counts}"',
            "reportCount": len(self.stats.reports),
        }

    def to_yaml(self, file_path: Path, is_maximize: bool = False) -> None:
        object_to_yaml(self.to_dict(is_maximize), file_path)

    def to_json(self, file_path: Path, is_maximize: bool = False) -> None:
        object_to_json(self.to_dict(is_maximize), file_path)
