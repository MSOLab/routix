import logging
import traceback
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Generic, Sequence, TypeVar

from ..elapsed_timer import ElapsedTimer
from ..type_defs import ParametersT, RunMode
from .single_instance_runner import SingleInstanceRunnerT


class MultiInstanceRunner(Generic[ParametersT, SingleInstanceRunnerT], ABC):
    """
    Abstract runner to orchestrate solving a set of instances with a given runner class.
    """

    mode: RunMode

    def __init__(
        self,
        s_i_runner_class: type[SingleInstanceRunnerT],
        instances: Sequence[ParametersT],
        shared_param_dict: dict,
        subroutine_flow: Any,
        stopping_criteria: Any,
        output_dir: Path,
        output_metadata: dict[str, Any],
        mode: RunMode = RunMode.FULL_RUN,
        **kwargs: Any,
    ) -> None:
        self.e_timer = ElapsedTimer()
        """Elapsed timer for multi-instance run."""

        # Runner class
        self.s_i_runner_class = s_i_runner_class

        # Instance data
        self.instances = instances
        self.shared_param_dict = shared_param_dict

        # Algorithm data
        self.subroutine_flow = subroutine_flow
        self.stopping_criteria = stopping_criteria

        # Output configuration
        self.output_dir = output_dir
        self.output_metadata = output_metadata

        # Execution configuration
        self.mode = mode

        self.runners: list[SingleInstanceRunnerT] = []
        self.results: list[Any] = []

        self._set_start_dt()
        self._init_working_dir()

    def _set_start_dt(self) -> None:
        """
        Sets the start date-time for the elapsed timer.
        If the start date-time is already in output_metadata, it uses that.
        Otherwise, it initializes the start date-time from the elapsed timer.
        """
        if dt := self.output_metadata.get("start_dt"):
            self.e_timer.set_start_time(dt)
        else:
            self.output_metadata["start_dt"] = self.e_timer.get_formatted_start_dt()

    def _init_working_dir(self) -> None:
        """
        Initialize the working directory for the multi-instance run.

        The working directory is the same as the output directory provided.
        """
        self.working_dir = self.output_dir
        self.working_dir.mkdir(parents=True, exist_ok=True)

    def run(self):
        self.runners.clear()
        self.results.clear()

        # Pre-create all runner instances
        for instance in self.instances:
            runner = self.s_i_runner_class(
                instance=instance,
                shared_param_dict=self.shared_param_dict,
                subroutine_flow=self.subroutine_flow,
                stopping_criteria=self.stopping_criteria,
                output_dir=self.output_dir,
                output_metadata=self.output_metadata,
                mode=self.mode,
            )
            self.runners.append(runner)

        for idx, runner in enumerate(self.runners):
            try:
                result = runner.run()
            except Exception as e:
                logging.error(f"Error in instance {idx}: {e}")
                traceback.print_exc()
                result = None
            self.results.append(result)

        return self.post_run_process()

    @abstractmethod
    def post_run_process(self) -> Any:
        """
        Post-processes the results after running all instances.
        This method should be implemented in subclasses to handle specific post-run logic.
        """
        ...


MultiInstanceRunnerT = TypeVar("MultiInstanceRunnerT", bound=MultiInstanceRunner)
"""
Type variable for MultiInstanceRunner, allowing methods to specify
that they return or accept an instance of MultiInstanceRunner or its subclasses.
"""
