from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence

from .dynamic_data_object import DynamicDataObject
from .elapsed_timer import ElapsedTimer
from .experiment_summary import ExperimentSummary
from .subroutine_flow_validator import SubroutineFlowValidator


class SubroutineController(ABC):
    timer: ElapsedTimer

    experiment_summary: ExperimentSummary

    stopping_criteria: DynamicDataObject
    __subroutine_flow: DynamicDataObject
    __method_call_log: list[dict[str, Any]]
    """A list of dictionaries containing method call logs."""

    def __init__(
        self,
        name: str,
        stopping_criteria: DynamicDataObject,
        subroutine_flow: DynamicDataObject,
        start_dt: datetime | None = None,
    ):
        # Check the validity of subroutine flow
        validator = SubroutineFlowValidator(self.__class__)
        validator.validate(subroutine_flow)

        # Set the timer
        self.timer = ElapsedTimer()
        if start_dt is not None:
            self.timer.set_start_time(start_dt)
        else:
            self.timer.set_start_time_as_now()

        # Set summary
        self.experiment_summary = ExperimentSummary(name)

        self.stopping_criteria = stopping_criteria
        self.__subroutine_flow = subroutine_flow
        self.__method_call_log = []

    def set_working_dir(self, dir_path: str):
        self.__working_dir_path = Path(dir_path)

    def run(self):
        self.execute_routine(self.__subroutine_flow)
        self.post_run_process()

    def execute_routine(self, routine_data: DynamicDataObject):
        if isinstance(routine_data, Sequence):  # is a list or tuple
            for subroutine_data in routine_data:
                self.execute_routine(subroutine_data)
        else:  # is an dict-like object
            if self.is_stopping_condition():
                return
            kwargs_dict: dict = routine_data.to_obj()
            method_name = kwargs_dict.pop("method_name")
            self.call_method(method_name, **kwargs_dict)

    def call_method(self, method_name: str, **kwargs):
        """Call a method by its name and log the execution time.

        Args:
            method_name (str): The name of the method to call.
            **kwargs: Any: Additional keyword arguments to pass to the method.

        Raises:
            AttributeError: If the method does not exist in the class.
        """
        if not hasattr(self, method_name):
            raise AttributeError(
                f"{self.__class__.__name__} has no attribute {method_name}"
            )
        method_start_sec = self.timer.get_elapsed_sec()

        self.experiment_summary.record_method_call(method_name)
        try:
            getattr(self, method_name)(**kwargs)
        except Exception as e:
            print(f"[Error] Method {method_name} failed: {e}")
            self.__add_method_call_log_entry(
                method_name=method_name,
                start_sec=method_start_sec,
                elapsed_sec=0,
                kwargs=kwargs,
                error=str(e),
            )
            raise

        elapsed_sec = self.timer.get_elapsed_sec() - method_start_sec
        self.__add_method_call_log_entry(
            method_name=method_name,
            start_sec=method_start_sec,
            elapsed_sec=elapsed_sec,
            kwargs=kwargs,
        )

    def __add_method_call_log_entry(self, **kwargs):
        self.__method_call_log.append(kwargs)

    def get_method_call_log(self) -> list[dict[str, Any]]:
        """Get the method call log.

        Returns:
            list[dict[str, Any]]: A list of dictionaries containing method call logs.
        """
        return self.__method_call_log.copy()

    @abstractmethod
    def is_stopping_condition(self) -> bool:
        pass

    @abstractmethod
    def post_run_process(self):
        """Post-process the results after running the subroutine flow."""
        pass

    def repeat(self, n_repeats: int, routine_data: DynamicDataObject):
        """
        Repeat a subroutine flow n_repeats times.

        Args:
            n_repeats (int): Number of repetitions
            routine_data (DynamicDataObject): A single subroutine
                or a list of subroutines
        """
        for i in range(n_repeats):
            if self.is_stopping_condition():
                print(
                    f"[Repeat] Stopping condition met at iteration {i + 1}/{n_repeats}."
                )
                break
            print(f"[Repeat] Starting repeat {i + 1}/{n_repeats}")
            ddo = DynamicDataObject.from_obj(routine_data)
            self.execute_routine(ddo)
