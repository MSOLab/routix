import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Generic, Sequence, TypeVar

from ..elapsed_timer import ElapsedTimer
from ..type_defs import ParametersT, RunMode
from .multi_instance_runner import MultiInstanceRunnerT
from .single_instance_runner import SingleInstanceRunnerT


class MultiScenarioRunner(
    Generic[ParametersT, SingleInstanceRunnerT, MultiInstanceRunnerT], ABC
):
    """
    Abstract runner to orchestrate running multiple scenarios, where each scenario
    is a set of instances executed by a MultiInstanceRunner.
    """

    mode: RunMode

    def __init__(
        self,
        m_i_runner_class: type[MultiInstanceRunnerT],
        s_i_runner_class: type[SingleInstanceRunnerT],
        instances: Sequence[ParametersT],
        shared_param_dict: dict,
        scenario_configs: Sequence[dict[str, Any]],
        output_dir: Path,
        base_output_metadata: dict[str, Any],
        mode: RunMode = RunMode.FULL_RUN,
        **kwargs: Any,
    ) -> None:
        # Set up the elapsed timer
        self.e_timer = ElapsedTimer()

        # Runner classes
        self.m_i_runner_class = m_i_runner_class
        self.s_i_runner_class = s_i_runner_class

        # Instance data
        self.instances = instances
        self.shared_param_dict = shared_param_dict

        # Scenario configurations
        self.scenario_configs = scenario_configs

        # Output configuration
        self.output_dir = output_dir
        self.base_output_metadata = base_output_metadata

        # Execution configuration
        self.mode = mode

        self.kwargs = kwargs

        self.runners: list[MultiInstanceRunnerT] = []
        self.results: list[Any] = []

        self._set_start_dt()

    def _set_start_dt(self) -> None:
        """
        Sets the start date-time for the elapsed timer.
        If the start date-time is already in output_metadata, it uses that.
        Otherwise, it initializes the start date-time from the elapsed timer.
        """
        if dt := self.base_output_metadata.get("start_dt"):
            self.e_timer.set_start_time(dt)
        else:
            self.base_output_metadata["start_dt"] = (
                self.e_timer.get_formatted_start_dt()
            )

    def run(self):
        """
        Executes each scenario sequentially.
        """
        self.runners.clear()
        self.results.clear()

        for i, scenario_config in enumerate(self.scenario_configs):
            logging.info(
                f"--- Starting Scenario {i + 1}/{len(self.scenario_configs)} ---"
            )
            logging.info(f"Scenario Config: {scenario_config}")

            subroutine_flow = scenario_config.get("subroutine_flow")
            stopping_criteria = scenario_config.get("stopping_criteria")

            if subroutine_flow is None or stopping_criteria is None:
                logging.warning(
                    f"Skipping scenario {i + 1} due to missing 'subroutine_flow' or 'stopping_criteria'."
                )
                continue

            # Use a specific output subdir from config, or create a default one
            scenario_output_dir = self.output_dir / f"scenario_{i + 1}"
            if "output_subdir" in scenario_config:
                scenario_output_dir = self.output_dir / str(
                    scenario_config["output_subdir"]
                )

            scenario_output_dir.mkdir(parents=True, exist_ok=True)

            multi_instance_runner = self.m_i_runner_class(
                s_i_runner_class=self.s_i_runner_class,
                instances=self.instances,
                shared_param_dict=self.shared_param_dict,
                subroutine_flow=subroutine_flow,
                stopping_criteria=stopping_criteria,
                output_dir=scenario_output_dir,
                output_metadata=self.base_output_metadata.copy(),
                mode=self.mode,
                **self.kwargs,
            )

            self.runners.append(multi_instance_runner)
            try:
                result = multi_instance_runner.run()
                self.results.append(result)
            except Exception as e:
                logging.error(f"Error in scenario {i + 1}: {e}", exc_info=True)
                self.results.append(None)

            logging.info(
                f"--- Finished Scenario {i + 1}/{len(self.scenario_configs)} ---"
            )

        return self.post_run_process()

    @abstractmethod
    def post_run_process(self) -> Any:
        """
        Post-processes the results after running all scenarios.
        This method should be implemented in subclasses to handle specific post-run logic,
        such as aggregating results from all scenarios.
        """
        ...


MultiScenarioRunnerT = TypeVar("MultiScenarioRunnerT", bound=MultiScenarioRunner)
