from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Generic, Optional, Sequence, TypeVar

from .constants import SubroutineFlowKeys
from .dynamic_data_object import DynamicDataObject
from .elapsed_timer import ElapsedTimer
from .experiment_summary import ExperimentSummary

StoppingCriteriaT = TypeVar("StoppingCriteriaT", bound=DynamicDataObject)


class SubroutineController(Generic[StoppingCriteriaT], ABC):
    """
    Base class for subroutine controllers using routine name context stack.
    """

    timer: ElapsedTimer
    """
    Timer to measure elapsed time during the experiment.
    This is set to the current time when the experiment starts.
    """

    experiment_summary: ExperimentSummary
    """Summary of the experiment, including method call logs and elapsed time."""

    stopping_criteria: StoppingCriteriaT
    """Stopping criteria for the experiment."""

    _subroutine_flow: DynamicDataObject
    _method_call_log: list[dict[str, Any]]
    """A list of dictionaries containing method call logs."""
    _routine_name_stack: list[str]
    """Stack of routine names to keep track of the current context."""

    _random_seed: Optional[int]
    """Random seed for reproducibility."""

    def __init__(
        self,
        name: str,
        subroutine_flow: DynamicDataObject,
        stopping_criteria: StoppingCriteriaT,
        start_dt: datetime | None = None,
    ):
        # Set the timer
        self.timer = ElapsedTimer()
        if start_dt is not None:
            self.timer.set_start_time(start_dt)
        else:
            self.timer.set_start_time_as_now()
        self.experiment_summary = ExperimentSummary(name)
        self._subroutine_flow = subroutine_flow
        self.stopping_criteria = stopping_criteria

        self._working_dir_path: Path | None = None
        self._routine_name_stack = []
        self._method_call_log = []

        self._random_seed = None

    def set_working_dir(self, dir_path: Path | str):
        """
        Set the working directory for this controller.
        This directory is used to store output files related to the experiment.
        - If the directory does not exist, it will be created.
        - If the directory already exists, it will not be overwritten.
        """
        self._working_dir_path = Path(dir_path)
        self._working_dir_path.mkdir(parents=True, exist_ok=True)

    def get_current_routine_name(self) -> str:
        return self._routine_name_stack[-1] if self._routine_name_stack else "unknown"

    def get_file_path_for_subroutine(self, filename_suffix: str) -> Path:
        routine_name = self.get_current_routine_name()
        if self._working_dir_path is None:
            raise AttributeError("Working directory path is not set.")
        return self._working_dir_path / (routine_name + filename_suffix)

    def run(self):
        self.execute_routine(self._subroutine_flow)
        self.post_run_process()

    def execute_routine(self, routine_data: DynamicDataObject, prefix: str = ""):
        if isinstance(routine_data, Sequence) and not isinstance(
            routine_data, (str, bytes)
        ):
            for i, subroutine_data in enumerate(routine_data, start=1):
                name_prefix = f"{prefix}.{i}" if prefix else str(i)
                self.execute_routine(subroutine_data, prefix=name_prefix)
        else:  # is an dict-like object
            if self.is_stopping_condition():
                return

            method_name, kwargs_dict = SubroutineFlowKeys.parse_step(
                routine_data.to_obj()
            )

            routine_name = f"{prefix}_{method_name}" if prefix else method_name
            self._routine_name_stack.append(routine_name)
            self.call_method(method_name, **kwargs_dict)
            self._routine_name_stack.pop()

    def call_method(self, method_name: str, **kwargs: dict[str, Any]):
        if not hasattr(self, method_name):
            raise AttributeError(
                f"{self.__class__.__name__} has no attribute {method_name}"
            )
        method_start_sec = self.timer.get_elapsed_sec()
        self.experiment_summary.record_method_call(method_name)

        log_entry: dict[str, Any] = {
            "routine_name": self.get_current_routine_name(),
            "method": method_name,
            "start_sec": method_start_sec,
            "kwargs": kwargs,
        }
        try:
            getattr(self, method_name)(**kwargs)
        except Exception as e:
            elapsed_sec = self.timer.get_elapsed_sec() - method_start_sec
            log_entry["elapsed_sec"] = elapsed_sec
            log_entry["error"] = str(e)
            self._add_method_call_log_entry(log_entry)
            raise

        elapsed_sec = self.timer.get_elapsed_sec() - method_start_sec
        log_entry["elapsed_sec"] = elapsed_sec
        self._add_method_call_log_entry(log_entry)

    def _add_method_call_log_entry(self, log_entry: dict[str, Any]):
        self._method_call_log.append(log_entry)

    def get_method_call_log(self) -> list[dict[str, Any]]:
        return self._method_call_log.copy()

    @abstractmethod
    def is_stopping_condition(self) -> bool:
        pass

    @abstractmethod
    def post_run_process(self):
        pass

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
    def random_seed(self) -> Optional[int]:
        """
        Returns the current random seed.

        Returns:
            Optional[int]: The random seed if set, otherwise None.
        """
        return self._random_seed

    def repeat(self, n_repeats: int, routine_data: DynamicDataObject):
        """
        Repeats the execution of a routine a specified number of times.

        Args:
            n_repeats (int): Number of times to repeat the routine.
            routine_data (DynamicDataObject): The routine data to be executed.
        """
        last_routine_name = self.get_current_routine_name()
        zero_fill_width = len(str(n_repeats))
        for i in range(n_repeats):
            if self.is_stopping_condition():
                print(
                    f"[Repeat] Stopping condition met at iteration {i + 1}/{n_repeats}."
                )
                break
            print(f"[Repeat] Starting repeat {i + 1}/{n_repeats}")

            prefix = f"{last_routine_name}-{str(i + 1).zfill(zero_fill_width)}"
            self._routine_name_stack.append(prefix)
            self.execute_routine(
                DynamicDataObject.from_obj(routine_data), prefix=prefix
            )
            self._routine_name_stack.pop()
