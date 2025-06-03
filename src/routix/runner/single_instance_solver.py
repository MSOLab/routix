from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Generic, TypeVar

from routix import ElapsedTimer, SubroutineController

ProblemT = TypeVar("ProblemT")  # Type for the problem instance
ControllerT = TypeVar("ControllerT", bound=SubroutineController)


class SingleInstanceSolver(Generic[ProblemT, ControllerT], ABC):
    """
    Abstract runner for a single problem instance.
    """

    instance: ProblemT
    ctrlr: ControllerT

    def __init__(
        self,
        instance: ProblemT,
        shared_params: dict,
        subroutine_flow: Any,
        stopping_criteria: Any,
        output_dir: Path,
        output_metadata: dict[str, Any],
    ):
        # Set up the elapsed timer
        self.e_timer = ElapsedTimer()
        if dt := output_metadata.get("start_dt"):
            self.e_timer.set_start_time(dt)

        # Instance data
        self.instance = instance
        self.shared_params = shared_params
        # Algorithm data
        self.subroutine_flow = subroutine_flow
        self.stopping_criteria = stopping_criteria
        # Output data
        self.output_dir = output_dir
        self.output_metadata = output_metadata

        # Alias
        self.ins_name = getattr(instance, "name", None)

        self._prepare_output_directory()

    def _prepare_output_directory(self) -> None:
        """
        Prepare the output directory for the instance run.
        """
        self.output_dir_instance = (
            self.output_dir / self.e_timer.get_formatted_start_dt()
        )
        if self.ins_name is not None:
            self.output_dir_instance = self.output_dir_instance / self.ins_name
        try:
            self.output_dir_instance.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise RuntimeError(
                f"Could not create output directory: {self.output_dir_instance}"
            ) from e

    def solve(self) -> None:
        """
        Solve the instance by running the controller and performing post-run processing.
        """
        self.run()
        self.post_run_process()

    def run(self):
        """
        Run the instance using the initialized controller.
        """
        self.ctrlr = self.init_controller()
        self.ctrlr.set_working_dir(self.output_dir_instance)
        self.ctrlr.run()

    @abstractmethod
    def init_controller(self) -> ControllerT:
        """
        Initialize the controller with the given instance and parameters.
        This method should be implemented by subclasses.
        """
        pass

    @abstractmethod
    def post_run_process(self):
        """
        Post-run process to handle any finalization tasks.
        This method should be implemented by subclasses.
        """
        pass
