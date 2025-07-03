from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Generic, TypeVar

from ..elapsed_timer import ElapsedTimer
from ..subroutine_controller import SubroutineControllerT
from ..type_defs import ParametersT


class SingleInstanceRunner(Generic[ParametersT, SubroutineControllerT], ABC):
    """Abstract runner for a single problem instance."""

    ctrlr: SubroutineControllerT

    working_dir: Path
    """Working directory for the instance run."""

    def __init__(
        self,
        instance: ParametersT,
        shared_param_dict: dict,
        subroutine_flow: Any,
        stopping_criteria: Any,
        output_dir: Path,
        output_metadata: dict[str, Any],
    ):
        self.e_timer = ElapsedTimer()
        """Elapsed timer for the single instance run."""
        if dt := output_metadata.get("start_dt"):
            self.e_timer.set_start_time(dt)

        # Instance data

        self.instance = instance
        """Problem instance's parameters."""

        self.shared_param_dict = shared_param_dict
        """Shared parameters for a group of the problem."""

        # Algorithm data

        self.subroutine_flow = subroutine_flow
        """The sequence of subroutines together with arguments for each."""
        self.stopping_criteria = stopping_criteria
        """Data to define when to halt the run."""

        # Output data

        self.output_dir = output_dir
        self.output_metadata = output_metadata

        # Alias
        self.ins_name = getattr(instance, "name", None)

        self._init_working_dir()

    def _init_working_dir(self) -> None:
        """
        Initialize the working directory for the instance run.
        This method creates a directory structure based on the output directory,
        elapsed timer start time, and instance name if available.

        - If the output directory name does not match the formatted start date-time,
        it creates a subdirectory with the formatted start date-time.
        - If an instance name is provided, it creates a further subdirectory for the instance.
        """
        self.working_dir = self.output_dir
        if self.output_dir.name != self.e_timer.get_start_dt_for_dir_name():
            self.working_dir /= self.e_timer.get_start_dt_for_dir_name()
        if self.ins_name is not None:
            self.working_dir /= self.ins_name
        self.working_dir.mkdir(parents=True, exist_ok=True)

    def run(self):
        """Run the instance using the initialized controller."""

        self.ctrlr = self.get_controller()
        self.ctrlr.set_working_dir(self.working_dir)

        single_instance_skip_run_do_post_process = self.output_metadata.get(
            "single_instance_skip_run_do_post_process", False
        )
        if single_instance_skip_run_do_post_process:
            # If skip run is set, skip the run and directly do post-process
            return self.post_run_process()

        self.ctrlr.run()

        return self.post_run_process()

    @abstractmethod
    def get_controller(self) -> SubroutineControllerT:
        """
        Return the controller with the given instance and parameters.
        This method should be implemented by subclasses.

        Returns:
            SubroutineControllerT: An instance of the subroutine controller
        """
        ...

    @abstractmethod
    def post_run_process(self):
        """
        Define process after subroutine controller run.
        This method should be implemented by subclasses.

        For example, you may

        - write the solution and statistics into files.
        - plot objective progress log or draw a gantt chart.

        If self.output_metadata["single_instance_skip_run_do_post_process"] exists and is True,
        this method will be called without running the controller.
        """
        ...


SingleInstanceRunnerT = TypeVar("SingleInstanceRunnerT", bound=SingleInstanceRunner)
"""
Type variable for SingleInstanceRunner, allowing methods to specify
that they return or accept an instance of SingleInstanceRunner or its subclasses.
"""
