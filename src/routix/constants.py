from typing import Any


class SubroutineFlowKeys:
    METHOD = "method"
    KWARGS = "params"

    @staticmethod
    def parse_step(step_dict: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        method_name_key = SubroutineFlowKeys.METHOD
        if method_name_key not in step_dict:
            raise ValueError("Method name not found in step data.")
        method_name = step_dict[method_name_key]

        kwargs_dict = (
            step_dict[SubroutineFlowKeys.KWARGS]
            if SubroutineFlowKeys.KWARGS in step_dict
            else {k: v for k, v in step_dict.items() if k != method_name_key}
        )

        return method_name, kwargs_dict
