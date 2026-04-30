from typing import Any, Final


class SubroutineFlowKeys:
    METHOD: Final = "method"
    KWARGS: Final = "params"

    @staticmethod
    def parse_step(step_dict: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        method_name_key = SubroutineFlowKeys.METHOD
        if method_name_key not in step_dict:
            raise ValueError(f"Method name '{method_name_key}' not found in step data.")
        method_name = step_dict[method_name_key]

        kwargs_dict = (
            step_dict[SubroutineFlowKeys.KWARGS]
            if SubroutineFlowKeys.KWARGS in step_dict
            else {k: v for k, v in step_dict.items() if k != method_name_key}
        )

        return method_name, kwargs_dict


class SubroutineReportStatisticsKeys:
    """Keys for the dictionary representation of SubroutineReportStatistics."""

    INSTANCE_NAME: Final = "insName"
    FOUND_FEASIBLE_SOL: Final = "foundFeasibleSol"
    TOTAL_ELAPSED_TIME: Final = "totalElapsedTime"
    FIRST_OBJ: Final = "firstObj"
    FIRST_BOUND: Final = "firstBound"
    BEST_OBJ: Final = "bestObj"
    BEST_BOUND: Final = "bestBound"
    IMPROVEMENT_RATIO: Final = "improvementRatio"
    METHOD_CALL_COUNTS: Final = "methodCallCounts"
    REPORT_COUNT: Final = "reportCount"
