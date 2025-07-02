import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Generic, Sequence, TypeVar
from warnings import warn

from .constants import SubroutineFlowKeys
from .dynamic_data_object import DynamicDataObject
from .elapsed_timer import ElapsedTimer
from .method_context_manager import MethodContextManager
from .report import (
    SubroutineReportRecorder,
    SubroutineReportT,
)
from .stopping_criteria import StoppingCriteriaT


class SubroutineController(Generic[StoppingCriteriaT, SubroutineReportT], ABC):
    """
    Base class for subroutine controllers using routine name context stack.
    """

    def __init__(
        self,
        name: str,
        subroutine_flow: DynamicDataObject,
        stopping_criteria: StoppingCriteriaT,
        start_dt: datetime | None = None,
    ):
        # Set the timer
        e_timer = ElapsedTimer()
        if start_dt is not None:
            e_timer.set_start_time(start_dt)
        else:
            e_timer.set_start_time_as_now()

        # Algorithm data
        self._subroutine_flow = subroutine_flow
        """The sequence of subroutines to be executed in the experiment."""
        self.stopping_criteria = stopping_criteria
        """Stopping criteria for the experiment."""

        # Output data
        self.report_recorder: SubroutineReportRecorder[SubroutineReportT] = (
            SubroutineReportRecorder(name)
        )
        """Counts method calls and records subroutine reports during experiment execution."""

        # Subroutine controller state
        self.timer = e_timer
        """
        Timer to measure elapsed time during the experiment.
        This is set to the current time when the experiment starts.
        """
        self._working_dir_path: Path | None = None
        """Path to the working directory where output files are stored."""
        self._method_context_mgr = MethodContextManager()
        """
        Context manager for method calls, used to track the current routine name
        and manage method call contexts.
        """
        self._random_seed: int | None = None
        """Random seed for reproducibility."""

    def set_working_dir(self, dir_path: Path | str):
        """
        Set the working directory for this controller.
        This directory is used to store output files related to the experiment.
        - If the directory does not exist, it will be created.
        - If the directory already exists, it will not be overwritten.
        """
        self._working_dir_path = Path(dir_path)
        self._working_dir_path.mkdir(parents=True, exist_ok=True)

    def _get_call_context_of_current_method(self) -> str:
        """
        Returns:
            str: A string representing the current method context,
            formatted as "count-name.count-name..." for each name in the call stack.
        """
        return self._method_context_mgr.context_of_current_method

    def get_current_routine_name(self) -> str:
        warn(
            "get_current_routine_name() is deprecated."
            " Use _get_context_of_current_method() instead."
        )
        return self._get_call_context_of_current_method()

    def get_file_path_for_subroutine(self, filename_suffix: str) -> Path:
        """Get the file path for a subroutine output file.

        - If the working directory is set, the file path is constructed by
          combining the working directory path with the current method context
          name and the provided filename suffix.
        - If the working directory is not set, an AttributeError is raised.

        This method is useful for generating file paths for output files related
        to the execution of subroutines in the experiment.

        Args:
            filename_suffix (str): The suffix to append to the file name.

        Raises:
            AttributeError: If the working directory path is not set.

        Returns:
            Path: The constructed file path for the subroutine output file.
        """

        if self._working_dir_path is None:
            raise AttributeError("Working directory path is not set.")
        filename = self._get_call_context_of_current_method() + filename_suffix
        return self._working_dir_path / filename

    def run(self):
        self._run_flow(self._subroutine_flow)
        self.post_run_process()

    def _run_flow(self, routine_data: DynamicDataObject):
        """
        Runs the subroutine flow defined by routine_data.
        Handles both sequences and single subroutine steps.
        Checks stopping condition before each execution.

        Args:
            routine_data (DynamicDataObject): Subroutine flow data.
        """
        if isinstance(routine_data, Sequence) and not isinstance(
            routine_data, (str, bytes)
        ):
            for subroutine_data in routine_data:
                self._run_flow(subroutine_data)
        else:  # is an dict-like object
            if self.is_stopping_condition():
                return

            method_name, kwargs_dict = SubroutineFlowKeys.parse_step(
                routine_data.to_obj()
            )

            self._method_context_mgr.push(method_name)
            self._call_method(method_name, **kwargs_dict)
            self._method_context_mgr.pop()

    def _call_method(self, method_name: str, **kwargs: dict[str, Any]):
        """Dynamically calls a method by its name with the provided keyword arguments.

        This method:
        - Manages the context of method calls by pushing the method name onto the call stack.
        - Records the start time and logs the elapsed time for each method call.
        - Handles exceptions by logging errors and re-raising them.
        - Tracks the execution flow of the subroutine controller.
        - Records the method call in the experiment summary.

        Notes:
        - The method name must correspond to a valid method defined in the subclass.
        - Raises an AttributeError if the method does not exist.
        - Useful for executing subroutines defined in the subroutine flow of the experiment.
        """

        if not hasattr(self, method_name):
            raise AttributeError(
                f"{self.__class__.__name__} has no attribute {method_name}"
            )
        start_sec = self.timer.elapsed_sec
        self.report_recorder.increment_method_call_count(method_name)

        log_entry: dict[str, Any] = {
            "method": method_name,
            "call_context": self._get_call_context_of_current_method(),
            "start_sec": start_sec,
            "kwargs": kwargs,
        }
        try:
            getattr(self, method_name)(**kwargs)
        except Exception as e:
            end_sec = self.timer.elapsed_sec
            elapsed_sec = end_sec - start_sec
            log_entry["elapsed_sec"] = elapsed_sec
            log_entry["error"] = str(e)
            logging.error(str(log_entry))
            raise e

        end_sec = self.timer.elapsed_sec
        elapsed_sec = end_sec - start_sec
        log_entry["elapsed_sec"] = elapsed_sec
        logging.info(str(log_entry))

    @abstractmethod
    def is_stopping_condition(self) -> bool:
        """
        Checks if the stopping condition for the subroutine controller is met.
        This method should be implemented in subclasses.
        Utilizing stopping_criteria is recommended.

        Returns:
            bool: True if the stopping condition is met, False otherwise.
        """
        ...

    @abstractmethod
    def post_run_process(self):
        """
        Define processes after subroutine flow or stopping condition.
        This method should be implemented in subclasses.

        For example, you may check the incumbent solution's feasibility.
        """
        ...

    def set_random_seed(self, seed: int):
        """
        Sets the random seed for reproducibility.

        Args:
            seed (int): The seed value to set.
        """
        import random

        self._random_seed = seed
        random.seed(seed)

    @property
    def random_seed(self) -> int | None:
        """
        Returns the current random seed.

        Returns:
            int | None: The random seed if set, otherwise None.
        """
        return self._random_seed

    def repeat(self, n_repeats: int, routine_data: DynamicDataObject):
        """
        Repeats the execution of a routine a specified number of times.

        Args:
            n_repeats (int): Number of times to repeat the routine.
            routine_data (DynamicDataObject): The routine data to be executed.
        """

        subroutine_name = "reps"  # TODO: define how to manage this

        for i in range(n_repeats):
            if self.is_stopping_condition():
                logging.info(
                    f"[Repeat] Stopping condition met at iteration {i + 1}/{n_repeats}."
                )
                break
            logging.info(f"[Repeat] Starting repeat {i + 1}/{n_repeats}")

            self._method_context_mgr.push(subroutine_name)
            self._run_flow(DynamicDataObject.from_obj(routine_data))
            self._method_context_mgr.pop()


SubroutineControllerT = TypeVar("SubroutineControllerT", bound=SubroutineController)
"""
Type variable for SubroutineController, allowing methods to specify
that they return or accept an instance of SubroutineController or its subclasses.
"""
