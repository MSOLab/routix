import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Generic, Sequence, TypeVar

from ..elapsed_timer import ElapsedTimer
from ..type_defs import ParametersT
from .multi_instance_runner import MultiInstanceRunnerT
from .single_instance_runner import SingleInstanceRunnerT


class MultiScenarioRunner(
    Generic[ParametersT, SingleInstanceRunnerT, MultiInstanceRunnerT], ABC
):
    """
    Abstract runner to orchestrate running multiple scenarios, where each scenario
    is a set of instances executed by a MultiInstanceRunner.
    """

    def __init__(
        self,
        m_i_runner_class: type[MultiInstanceRunnerT],
        s_i_runner_class: type[SingleInstanceRunnerT],
        instances: Sequence[ParametersT],
        shared_param_dict: dict,
        scenario_configs: Sequence[dict[str, Any]],
        output_dir: Path,
        base_output_metadata: dict[str, Any],
    ):
        # Set up the elapsed timer
        self.e_timer = ElapsedTimer()

        # InstanceRunners
        self.m_i_runner_class = m_i_runner_class
        self.s_i_runner_class = s_i_runner_class

        # Instance data
        self.instances = instances
        self.shared_param_dict = shared_param_dict

        # Algorithm data
        self.scenario_configs = scenario_configs

        # Output data
        self.output_dir = output_dir
        self.base_output_metadata = base_output_metadata

        self.runners: list[MultiInstanceRunnerT] = []
        self.results: list[Any] = []

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

            # Each scenario might have its own subroutine_flow and stopping_criteria
            subroutine_flow = scenario_config.get("subroutine_flow")
            stopping_criteria = scenario_config.get("stopping_criteria")

            if subroutine_flow is None or stopping_criteria is None:
                logging.warning(
                    f"Skipping scenario {i + 1} due to missing 'subroutine_flow' or 'stopping_criteria'."
                )
                continue

            # Create a dedicated output directory for the scenario
            scenario_output_dir = self.output_dir / f"scenario_{i + 1}"
            scenario_output_dir.mkdir(parents=True, exist_ok=True)

            # Create and run a MultiInstanceRunner for the current scenario
            multi_instance_runner = self.m_i_runner_class(
                s_i_runner_class=self.s_i_runner_class,
                instances=self.instances,
                shared_param_dict=self.shared_param_dict,
                subroutine_flow=subroutine_flow,
                stopping_criteria=stopping_criteria,
                output_dir=scenario_output_dir,
                output_metadata=self.base_output_metadata.copy(),
            )

            self.runners.append(multi_instance_runner)
            try:
                result = multi_instance_runner.run()
                self.results.append(result)
            except Exception as e:
                logging.error(f"Error in scenario {i + 1}: {e}")
                self.results.append(None)

            logging.info(
                f"--- Finished Scenario {i + 1}/{len(self.scenario_configs)} ---"
            )

        return self.post_run_process()

    @abstractmethod
    def post_run_process(self):
        """
        Post-processes the results after running all scenarios.
        This method should be implemented in subclasses to handle specific post-run logic,
        such as aggregating results from all scenarios.
        """
        logging.info("Finished all scenarios. Aggregating results...")
        # Implementation for result aggregation goes here.
        pass


MultiScenarioRunnerT = TypeVar("MultiScenarioRunnerT", bound=MultiScenarioRunner)
