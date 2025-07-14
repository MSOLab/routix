from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Generic, TypeVar

from ..elapsed_timer import ElapsedTimer
from ..subroutine_controller import SubroutineControllerT
from ..type_defs import ParametersT, RunMode


class SingleInstanceRunner(Generic[ParametersT, SubroutineControllerT], ABC):
    """Abstract runner for a single problem instance."""

    ctrlr: SubroutineControllerT
    working_dir: Path
    mode: RunMode

    def __init__(
        self,
        instance: ParametersT,
        shared_param_dict: dict,
        subroutine_flow: Any,
        stopping_criteria: Any,
        output_dir: Path,
        output_metadata: dict[str, Any],
        mode: RunMode = RunMode.FULL_RUN,
    ):
        self.e_timer = ElapsedTimer()
        """Elapsed timer for single-instance run."""
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

        # Output configuration

        self.output_dir = output_dir
        """Output directory for the instance run."""
        self.output_metadata = output_metadata
        """Metadata for the output, such as start date-time and other information."""

        # Execution configuration

        self.mode = mode

        # Alias

        self.ins_name = getattr(instance, "name", None)
        """Alias for the instance name, if available."""
        self._init_working_dir()

    def _init_working_dir(self) -> None:
        """
        Initialize the working directory for the instance run.

        The working directory is a subdirectory of the output_dir, named after the instance.
        """
        self.working_dir = self.output_dir
        if self.ins_name is not None:
            self.working_dir /= self.ins_name
        self.working_dir.mkdir(parents=True, exist_ok=True)

    def run(self):
        """
        Run the subroutine controller for the instance.

        - This method initializes the controller and runs it if the mode is FULL_RUN.
        - If the mode is POST_PROCESS_ONLY, it skips the controller run and directly
        calls the post_run_process method.
        """
        if self.mode == RunMode.FULL_RUN:
            self.ctrlr = self.get_controller()
            self.ctrlr.set_working_dir(self.working_dir)
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
    def post_run_process(self) -> Any:
        """
        Define process after subroutine controller run.
        This method should be implemented by subclasses.

        For example, you may

        - write the solution and statistics into files.
        - plot objective progress log or draw a gantt chart.

        If self.mode is RunMode.POST_PROCESS_ONLY,
        this method will be called without running the controller.
        """
        ...


SingleInstanceRunnerT = TypeVar("SingleInstanceRunnerT", bound=SingleInstanceRunner)
"""
Type variable for SingleInstanceRunner, allowing methods to specify
that they return or accept an instance of SingleInstanceRunner or its subclasses.
"""
